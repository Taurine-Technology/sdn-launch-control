"""
Production-Grade Model Management System

This module provides a high-performance, database-driven system for managing
multiple classification models with Redis-based state management for instant changes.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import keras
from asgiref.sync import sync_to_async, async_to_sync
import numpy as np
import redis

from .models import ModelConfiguration, ModelState, ClassificationStats
from .state_manager import state_manager
from utils.ip_lookup_service import get_asn_from_ip

logger = logging.getLogger(__name__)

# DNS Redis key - same as in dns_loader.py
REDIS_DNS_KEY = "dns_servers:ip_set"


class ModelManager:
    """
    Production-grade model manager with database persistence and Redis caching.
    """
    
    def __init__(self):
        self.loaded_models: Dict[str, Any] = {}
        # Initialize Redis connection for DNS lookups (separate from state_manager)
        self._init_redis_connection()
        
        # Classification stats are now tracked in Redis (shared across processes)
        # No in-memory counters needed - using state_manager.increment_classification_stat()
        
        self._initialize_from_database()
    
    def _init_redis_connection(self):
        """Initialize Redis connection for DNS server lookups"""
        try:
            redis_host = getattr(settings, 'CHANNEL_REDIS_HOST', 'redis')
            redis_port = getattr(settings, 'CHANNEL_REDIS_PORT', 6379)
            self.redis_dns = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=1.0,  # 1 second to connect
                socket_timeout=1.0,          # 1 second per operation
                retry_on_timeout=True,       # Auto-retry once on timeout
                health_check_interval=30,    # Health check every 30s
                client_name="model-manager:dns-lookup"  # Identify in Redis CLIENT LIST
            )
            # Test connection
            self.redis_dns.ping()
            logger.debug("DNS Redis connection initialized successfully")
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError, redis.exceptions.RedisError):
            logger.exception("Failed to initialize DNS Redis connection")
            self.redis_dns = None
    
    def _with_fallback_categories(self, categories: List[str]) -> List[str]:
        """
        Ensure standard fallback categories exist, appending them to the end.
        
        IMPORTANT: Categories are appended to preserve model prediction indices.
        Model outputs are indexed by position, so we can't insert at the beginning.
        
        Args:
            categories: Original list of categories from model
            
        Returns:
            List with Unknown, DNS, and Apple appended if missing
        """
        out = list(categories)  # Create copy to avoid modifying original
        for category in ("Unknown", "DNS", "Apple"):
            if category not in out:
                out.append(category)
        return out
    
    def _initialize_from_database(self):
        """Initialize model manager from database"""
        try:
            # Load configurations from database (safe in async contexts)
            def _load_all_models():
                return list(ModelConfiguration.objects.all())
            db_models = async_to_sync(sync_to_async(_load_all_models, thread_sensitive=True))()
            
            # Cache configurations in Redis
            for model in db_models:
                config_dict = {
                    'name': model.name,
                    'display_name': model.display_name,
                    'model_type': model.model_type,
                    'model_path': model.model_path,
                    'input_shape': model.input_shape,
                    'num_categories': model.num_categories,
                    'confidence_threshold': model.confidence_threshold,
                    'description': model.description,
                    'version': model.version,
                    'is_active': model.is_active,
                    'categories': model.categories
                }
                state_manager.set_model_config(model.name, config_dict)
            
            # Set active model from database
            def _get_active_model():
                return ModelConfiguration.objects.filter(is_active=True).first()
            active_model = async_to_sync(sync_to_async(_get_active_model, thread_sensitive=True))()
            if active_model:
                state_manager.set_active_model(active_model.name)
                logger.debug(f"Active model set to: {active_model.name}")
                
                # Automatically load the active model
                self.load_model(active_model.name)
            else:
                logger.warning("No active model found in database")
                
        except Exception as e:
            logger.error(f"Error initializing from database: {e}")
            self._load_from_json_fallback()
    
    def _load_from_json_fallback(self):
        """Fallback to JSON configuration if database is not available"""
        json_config_path = os.path.join(settings.BASE_DIR, 'classifier/models_config.json')
        
        if os.path.exists(json_config_path):
            try:
                with open(json_config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Import models to database
                for model_key, model_data in config_data.get('models', {}).items():
                    self._create_model_from_json(model_key, model_data)
                
                logger.debug("Loaded models from JSON fallback")
                
            except Exception as e:
                logger.error(f"Error loading from JSON fallback: {e}")
    
    def _create_model_from_json(self, model_key: str, model_data: Dict[str, Any]):
        """Create a model configuration from JSON data"""
        try:
            model_path = os.path.join(settings.BASE_DIR, model_data['model_path'])
            
            # Create or update model configuration
            def _get_or_create_model():
                return ModelConfiguration.objects.get_or_create(
                    name=model_key,
                    defaults={
                        'display_name': model_data['name'],
                        'model_type': model_data['model_type'],
                        'model_path': model_path,
                        'input_shape': model_data.get('input_shape', [225, 5]),
                        'num_categories': model_data['num_categories'],
                        'confidence_threshold': model_data.get('confidence_threshold', 0.7),
                        'description': model_data.get('description', ''),
                        'version': model_data.get('version', '1.0'),
                        'is_active': model_data.get('is_active', False),
                        'categories': model_data['categories']
                    }
                )
            model_config, created = async_to_sync(sync_to_async(_get_or_create_model, thread_sensitive=True))()
            
            if not created:
                # Update existing model
                model_config.display_name = model_data['name']
                model_config.model_type = model_data['model_type']
                model_config.model_path = model_path
                model_config.input_shape = model_data.get('input_shape', [225, 5])
                model_config.num_categories = model_data['num_categories']
                model_config.confidence_threshold = model_data.get('confidence_threshold', 0.7)
                model_config.description = model_data.get('description', '')
                model_config.version = model_data.get('version', '1.0')
                model_config.categories = model_data['categories']
                def _save():
                    model_config.save()
                async_to_sync(sync_to_async(_save, thread_sensitive=True))()
            
            # Cache in Redis
            config_dict = {
                'name': model_config.name,
                'display_name': model_config.display_name,
                'model_type': model_config.model_type,
                'model_path': model_config.model_path,
                'input_shape': model_config.input_shape,
                'num_categories': model_config.num_categories,
                'confidence_threshold': model_config.confidence_threshold,
                'description': model_config.description,
                'version': model_config.version,
                'is_active': model_config.is_active,
                'categories': model_config.categories
            }
            state_manager.set_model_config(model_key, config_dict)
            
        except Exception as e:
            logger.error(f"Error creating model from JSON: {e}")
    
    def load_model(self, model_name: str) -> bool:
        """
        Load a specific model into memory
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        # Check if already loaded
        if model_name in self.loaded_models:
            logger.debug(f"Model '{model_name}' already loaded")
            return True
        
        # Get configuration from Redis cache or database
        config_dict = state_manager.get_model_config(model_name)
        if not config_dict:
            # Try to get from database
            try:
                model_config = ModelConfiguration.objects.get(name=model_name)
                config_dict = {
                    'name': model_config.name,
                    'display_name': model_config.display_name,
                    'model_type': model_config.model_type,
                    'model_path': model_config.model_path,
                    'input_shape': model_config.input_shape,
                    'num_categories': model_config.num_categories,
                    'confidence_threshold': model_config.confidence_threshold,
                    'description': model_config.description,
                    'version': model_config.version,
                    'is_active': model_config.is_active,
                    'categories': model_config.categories
                }
                state_manager.set_model_config(model_name, config_dict)
            except ModelConfiguration.DoesNotExist:
                logger.error(f"Model '{model_name}' not found in database")
                return False
        
        try:
            model_path = config_dict['model_path']
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Load model based on type
            if config_dict['model_type'] == "keras_h5":
                model = keras.models.load_model(model_path)
            elif config_dict['model_type'] == "tensorflow_saved_model":
                model = keras.models.load_model(model_path)
            else:
                logger.error(f"Unsupported model type: {config_dict['model_type']}")
                return False
            
            # Store in memory
            self.loaded_models[model_name] = {
                'model': model,
                'config': config_dict,
                'class_names': config_dict['categories']
            }
            
            # Update Redis state
            state_manager.add_loaded_model(model_name)
            
            logger.debug(f"Successfully loaded model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model '{model_name}': {e}")
            return False
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            bool: True if model unloaded successfully, False otherwise
        """
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            state_manager.remove_loaded_model(model_name)
            logger.debug(f"Unloaded model: {model_name}")
            return True
        return False
    
    def set_active_model(self, model_name: str) -> bool:
        """
        Set the active model for classification (instant change)
        
        Args:
            model_name: Name of the model to activate
            
        Returns:
            bool: True if model activated successfully, False otherwise
        """
        # Check if model exists in database
        try:
            model_config = ModelConfiguration.objects.get(name=model_name)
        except ModelConfiguration.DoesNotExist:
            logger.error(f"Model '{model_name}' not found in database")
            return False
        
        # Load the model if not already loaded
        if not self.load_model(model_name):
            return False
        
        # Update database (this will automatically deactivate other models)
        model_config.is_active = True
        model_config.save()
        
        # Update Redis state (instant change)
        state_manager.set_active_model(model_name)
        
        logger.debug(f"Active model set to: {model_name}")
        
        # Validate that categories exist in database
        self._validate_model_categories(model_name)
        
        return True
    
    def _validate_model_categories(self, model_name: str):
        """
        Validate that categories for a model exist in the database
        
        Args:
            model_name: Name of the model to validate
        """
        try:
            from odl.models import Category
            
            # Get categories from Redis cache or database
            config_dict = state_manager.get_model_config(model_name)
            if not config_dict:
                model_config = ModelConfiguration.objects.get(name=model_name)
                expected_categories = set(model_config.categories)
            else:
                expected_categories = set(config_dict['categories'])
            
            # Get existing categories from database
            db_categories = set(Category.objects.values_list('name', flat=True))
            
            # Find missing categories
            missing_categories = expected_categories - db_categories
            
            if missing_categories:
                logger.warning(f"Missing categories for model '{model_name}': {missing_categories}")
                logger.warning("Run 'python manage.py populate_categories_from_model' to create missing categories")
            else:
                logger.debug(f"All categories for model '{model_name}' are present in database")
                
        except Exception as e:
            logger.error(f"Error validating categories for model '{model_name}': {e}")
    
    def get_active_model(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active model
        
        Returns:
            Dict containing model, config, and class_names, or None if no active model
        """
        active_model_name = state_manager.get_active_model()
        if not active_model_name:
            # Try to restore from database
            try:
                active_model_config = ModelConfiguration.objects.filter(is_active=True).first()
                if active_model_config:
                    logger.debug(f"Restoring active model from database: {active_model_config.name}")
                    state_manager.set_active_model(active_model_config.name)
                    active_model_name = active_model_config.name
            except Exception as e:
                logger.error(f"Error restoring active model from database: {e}")
                return None
        
        if not active_model_name or active_model_name not in self.loaded_models:
            # Try to load the model if it's not loaded
            if active_model_name and self.load_model(active_model_name):
                return self.loaded_models[active_model_name]
            return None
        
        return self.loaded_models[active_model_name]
    
    @property
    def active_model(self) -> Optional[str]:
        """Get the active model name from Redis"""
        active_model_name = state_manager.get_active_model()
        if not active_model_name:
            # Try to restore from database
            try:
                active_model_config = ModelConfiguration.objects.filter(is_active=True).first()
                if active_model_config:
                    logger.debug(f"Restoring active model from database: {active_model_config.name}")
                    state_manager.set_active_model(active_model_config.name)
                    return active_model_config.name
            except Exception as e:
                logger.error(f"Error restoring active model from database: {e}")
        return active_model_name
    
    def get_active_model_categories(self) -> List[str]:
        """
        Get categories from the active model configuration
        
        Returns:
            List of category names from the active model (always includes "Unknown", "DNS", and "Apple" for fallback)
        """
        active_model_name = state_manager.get_active_model()
        if not active_model_name:
            return []
        
        # Try Redis cache first
        config_dict = state_manager.get_model_config(active_model_name)
        if config_dict:
            categories = config_dict['categories']
        else:
            # Fallback to database
            try:
                model_config = ModelConfiguration.objects.get(name=active_model_name)
                categories = model_config.categories
            except ModelConfiguration.DoesNotExist:
                categories = []
        
        # Ensure standard fallback categories are always available
        return self._with_fallback_categories(categories)
    
    def get_model_categories(self, model_name: str) -> List[str]:
        """
        Get categories from a specific model configuration
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of category names from the specified model (always includes "Unknown", "DNS", and "Apple" for fallback)
        """
        # Try Redis cache first
        config_dict = state_manager.get_model_config(model_name)
        if config_dict:
            categories = config_dict['categories']
        else:
            # Fallback to database
            try:
                model_config = ModelConfiguration.objects.get(name=model_name)
                categories = model_config.categories
            except ModelConfiguration.DoesNotExist:
                categories = []
        
        # Ensure standard fallback categories are always available
        return self._with_fallback_categories(categories)
    
    def predict_flow(self, packet_arr: List[List[int]], client_ip_address: Optional[str] = None) -> Tuple[str, float]:
        """
        Predict flow classification using the active model
        
        Args:
            packet_arr: Packet array for classification
            client_ip_address: Optional client IP for ASN lookup
            
        Returns:
            Tuple of (prediction, time_elapsed)
        """
        import time
        
        active_model_data = self.get_active_model()
        if not active_model_data:
            raise ValueError("No active model available for prediction")
        
        model = active_model_data['model']
        config = active_model_data['config']
        class_names = active_model_data['class_names']
        
        # Ensure standard fallback categories are always available (appended to preserve indices)
        class_names = self._with_fallback_categories(class_names)
        
        start_time = time.time()
        
        # Prepare input data with dynamic shape from configuration
        input_shape = config['input_shape']
        if len(input_shape) == 2:
            # Reshape to (batch_size, *input_shape)
            packet_array = np.array(packet_arr).reshape(-1, *input_shape)
        else:
            # Fallback to default shape
            logger.error("[ModelManager] Fallback to default shape")
            packet_array = np.array(packet_arr).reshape(-1, 225, 5)
        
        x_test = packet_array.astype(int) / 255
        
        # Make prediction
        predictions = model.predict(x_test, verbose=0)
        y_prediction = np.argmax(predictions)
        
        end_time = time.time()
        time_elapsed = end_time - start_time
        
        # Get probabilities
        probabilities = predictions[0] if len(predictions.shape) > 1 else predictions
        
        # Log classification results
        # logger.info("**********************************************")
        # logger.info("Top 5 Classification Percentages:")
        # logger.info("**********************************************")
        
        # Create list of (class_name, probability) tuples and sort by probability
        class_probabilities = list(zip(class_names, probabilities))
        class_probabilities.sort(key=lambda x: x[1], reverse=True)
        
        # Log top 5
        # for i, (class_name, probability) in enumerate(class_probabilities[:5]):
        #     percentage = probability * 100
        #     logger.info(f"{i+1}. {class_name}: {percentage:.2f}%")
        
        logger.debug("**********************************************")
        
        # Confidence analysis
        max_probability = class_probabilities[0][1]
        second_highest_probability = class_probabilities[1][1] if len(class_probabilities) > 1 else 0
        
        # Check confidence thresholds
        high_confidence = max_probability > config['confidence_threshold']
        low_confidence = max_probability < 0.5
        
        # Check for multiple candidates
        multiple_candidates = (max_probability - second_highest_probability) < 0.2 and second_highest_probability > 0.3
        
        # Determine final prediction
        if high_confidence and not multiple_candidates:
            final_prediction = class_names[y_prediction]
            confidence_level = "HIGH"
        else:
            final_prediction = "Unknown"
            if low_confidence:
                confidence_level = "LOW"
            elif multiple_candidates:
                confidence_level = "MULTIPLE_CANDIDATES"
            else:
                confidence_level = "UNCERTAIN"
        
        # logger.info(f"Max Probability: {max_probability:.3f}")
        # logger.info(f"Second Highest: {second_highest_probability:.3f}")
        logger.debug(f"Confidence Level: {confidence_level}")
        logger.debug(f"Final Prediction: {final_prediction}")
        logger.debug("************************************************")
        
        # Track DNS and ASN usage
        dns_detected = False
        asn_used = False
        
        # Enhanced ASN-based category matching with DNS detection
        if client_ip_address and (final_prediction == "Unknown" or final_prediction == "QUIC"):
            try:
                # First check if it's a known DNS server IP
                dns_category = self._check_dns_ip(client_ip_address, class_names)
                if dns_category:
                    final_prediction = dns_category
                    dns_detected = True
                    logger.debug(f"DNS server detected: {client_ip_address} -> {dns_category}")
                    logger.debug("************************************************")
                    # Track stats before returning
                    self._increment_stats(confidence_level, time_elapsed, dns_detected=True, asn_used=False)
                    return final_prediction, time_elapsed
                
                # If not DNS, proceed with ASN lookup
                asn_info = get_asn_from_ip(client_ip_address)
                
                if asn_info:
                    logger.debug("**********************************************")
                    logger.debug("ASN Lookup Results for Enhanced Category Matching:")
                    logger.debug(f"Client IP: {client_ip_address}")
                    logger.debug(f"ASN: {asn_info['asn']}")
                    logger.debug(f"Organization: {asn_info['organization']}")
                    
                    # Enhanced category matching logic
                    organization_lower = asn_info['organization'].lower()
                    logger.debug(f"Available categories in model: {class_names}")
                    # original_prediction = final_prediction
                    
                    if final_prediction == "Unknown":
                        # Try to match ASN organization to available categories
                        matched_category = self._match_asn_to_category(organization_lower, class_names)
                        if matched_category:
                            final_prediction = matched_category
                            asn_used = True
                            logger.debug(f"ASN Match Found: '{asn_info['organization']}' -> '{matched_category}'")
                        else:
                            logger.debug(f"No ASN match found for '{asn_info['organization']}', keeping as 'Unknown'")
                    
                    elif final_prediction == "QUIC":
                        # Special QUIC handling with ASN matching
                        quic_category = self._match_quic_asn_to_category(organization_lower, class_names)
                        if quic_category:
                            final_prediction = quic_category
                            asn_used = True
                            logger.debug(f"QUIC ASN Match: '{asn_info['organization']}' -> '{quic_category}'")
                        else:
                            logger.debug(f"No QUIC ASN match found for '{asn_info['organization']}', keeping as 'QUIC'")
                    
                    logger.debug(f"Final Prediction After ASN Matching: {final_prediction}")
                    logger.debug("**********************************************")
                else:
                    logger.debug(f"ASN lookup failed for IP: {client_ip_address}")
            except Exception as e:
                logger.error(f"Error during ASN lookup for IP {client_ip_address}: {e}")
        
        # Track classification stats
        self._increment_stats(confidence_level, time_elapsed, dns_detected=dns_detected, asn_used=asn_used)
        
        return final_prediction, time_elapsed
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models with their status
        
        Returns:
            List of model information dictionaries
        """
        models_info = []
        
        # Get all models from database
        db_models = ModelConfiguration.objects.all()
        
        for model in db_models:
            # Check if model is loaded in memory
            is_loaded = model.name in self.loaded_models
            
            # Check if file exists
            file_exists = os.path.exists(model.model_path)
            
            model_info = {
                'name': model.name,
                'display_name': model.display_name,
                'model_type': model.model_type,
                'num_categories': model.num_categories,
                'categories': model.categories,
                'description': model.description,
                'version': model.version,
                'confidence_threshold': model.confidence_threshold,
                'is_active': model.is_active,
                'is_loaded': is_loaded,
                'file_exists': file_exists,
                'input_shape': model.input_shape
            }
            models_info.append(model_info)
        
        return models_info
    
    def add_model(self, config_dict: Dict[str, Any]) -> bool:
        """
        Add a new model configuration to database
        
        Args:
            config_dict: Dictionary containing model configuration
            
        Returns:
            bool: True if model added successfully, False otherwise
        """
        try:
            # Create model configuration in database
            model_config = ModelConfiguration.objects.create(
                name=config_dict['name'],
                display_name=config_dict['display_name'],
                model_type=config_dict['model_type'],
                model_path=config_dict['model_path'],
                input_shape=config_dict.get('input_shape', [225, 5]),
                num_categories=config_dict['num_categories'],
                confidence_threshold=config_dict.get('confidence_threshold', 0.7),
                description=config_dict.get('description', ''),
                version=config_dict.get('version', '1.0'),
                is_active=config_dict.get('is_active', False),
                categories=config_dict['categories']
            )
            
            # Cache in Redis
            state_manager.set_model_config(model_config.name, config_dict)
            
            logger.debug(f"Added model configuration: {model_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding model configuration: {e}")
            return False
    
    def remove_model(self, model_name: str) -> bool:
        """
        Remove a model configuration from database
        
        Args:
            model_name: Name of the model to remove
            
        Returns:
            bool: True if model removed successfully, False otherwise
        """
        try:
            # Unload if loaded
            self.unload_model(model_name)
            
            # Remove from database
            model_config = ModelConfiguration.objects.get(name=model_name)
            model_config.delete()
            
            # Clear from Redis cache
            # Note: Redis will auto-expire, but we could add a method to clear specific keys
            
            logger.debug(f"Removed model: {model_name}")
            return True
            
        except ModelConfiguration.DoesNotExist:
            logger.error(f"Model '{model_name}' not found in database")
            return False
        except Exception as e:
            logger.error(f"Error removing model: {e}")
            return False
    
    def _match_asn_to_category(self, organization_lower: str, available_categories: List[str]) -> Optional[str]:
        """
        Match ASN organization to available model categories
        
        Args:
            organization_lower: Lowercase organization name from ASN lookup
            available_categories: List of available categories in the model
            
        Returns:
            Matched category name or None if no match found
        """
        # Define ASN organization to category mappings
        asn_mappings = {
            'google': ['Google', 'GoogleServices', 'YouTube'],
            'youtube': ['YouTube'],
            'facebook': ['Facebook', 'FbookReelStory'],
            'meta': ['Facebook', 'FbookReelStory'],
            'instagram': ['Instagram'],
            'whatsapp': ['WhatsApp', 'WhatsAppFiles'],
            'amazon': ['AmazonAWS'],
            'microsoft': ['Microsoft'],
            'netflix': ['NetFlix'],
            'spotify': ['Spotify'],
            'tiktok': ['TikTok'],
            'huawei': ['HuaweiCloud'],
            'apple': ['Apple'],
            'cloudflare': ['Cloudflare'],
            'twitter': ['Twitter'],
            'snapchat': ['Snapchat'],
            'xiaomi': ['Xiaomi'],
            'gmail': ['GMail'],
            'microsoft office': ['Microsoft'],
            'office 365': ['Microsoft'],
            'azure': ['Microsoft'],
            'aws': ['AmazonAWS'],
            'amazon web services': ['AmazonAWS'],
            'google cloud': ['GoogleCloud'],
            'google docs': ['GoogleDocs'],
            'google drive': ['GoogleServices'],
            'google maps': ['GoogleServices'],
            'google play': ['GoogleServices'],
            'google photos': ['GoogleServices'],
            'google calendar': ['GoogleServices'],
            'google meet': ['GoogleServices'],
            'google chat': ['GoogleServices'],
            'google workspace': ['GoogleServices'],
            'g suite': ['GoogleServices'],
            'facebook messenger': ['Messenger'],
            'messenger': ['Messenger'],
            'facebook reels': ['FbookReelStory'],
            'facebook stories': ['FbookReelStory'],
            'instagram reels': ['FbookReelStory'],
            'instagram stories': ['FbookReelStory'],
            'whatsapp web': ['WhatsApp'],
            'whatsapp business': ['WhatsApp'],
            'whatsapp files': ['WhatsAppFiles'],
            'windows update': ['WindowsUpdate'],
            'microsoft update': ['WindowsUpdate'],
            'cybersec': ['Cybersec'],
            'cyber security': ['Cybersec'],
            'security': ['Cybersec'],
            'tls': ['TLS'],
            'ssl': ['TLS'],
            'http': ['HTTP'],
            'https': ['HTTP'],
            'bittorrent': ['BitTorrent'],
            'torrent': ['BitTorrent'],
            'ads': ['ADS_Analytic_Track'],
            'analytics': ['ADS_Analytic_Track'],
            'tracking': ['ADS_Analytic_Track'],
            'advertising': ['ADS_Analytic_Track'],
            # Remove 'unknown' mapping to avoid circular logic
            # 'unknown': ['Unknown']
        }
        
        # Try exact matches first
        for org_key, categories in asn_mappings.items():
            if org_key in organization_lower:
                logger.debug(f"Exact match found: '{org_key}' in '{organization_lower}'")
                # Find the first matching category that's available in the model
                for category in categories:
                    if category in available_categories:
                        logger.debug(f"Returning category '{category}' from exact match")
                        return category
                    else:
                        logger.debug(f"Category '{category}' not available in model")
        
        # Try partial matches for more flexible matching (word boundaries)
        for org_key, categories in asn_mappings.items():
            # Split both strings into words and check for word-level matches
            org_words = set(org_key.split())
            org_lower_words = set(organization_lower.replace('-', ' ').replace('_', ' ').split())
            
            # Check if any word from org_key appears as a complete word in organization_lower
            if org_words.intersection(org_lower_words):
                logger.debug(f"Partial match found: '{org_key}' words in '{organization_lower}'")
                for category in categories:
                    if category in available_categories:
                        logger.debug(f"Returning category '{category}' from partial match")
                        return category
                    else:
                        logger.debug(f"Category '{category}' not available in model")
        
        return None
    
    def _match_quic_asn_to_category(self, organization_lower: str, available_categories: List[str]) -> Optional[str]:
        """
        Special ASN matching for QUIC protocol with specific rules
        
        Args:
            organization_lower: Lowercase organization name from ASN lookup
            available_categories: List of available categories in the model
            
        Returns:
            Matched category name or None if no match found
        """
        # Special QUIC ASN mappings
        quic_asn_mappings = {
            'meta': 'FbookReelStory',
            'facebook': 'FbookReelStory',
            'google': 'YouTube',
            'youtube': 'YouTube'
        }
        
        # Check for exact matches first
        for org_key, category in quic_asn_mappings.items():
            if org_key in organization_lower and category in available_categories:
                return category
        
        # Check for partial matches
        for org_key, category in quic_asn_mappings.items():
            if any(word in organization_lower for word in org_key.split()) and category in available_categories:
                return category
        
        return None
    
    def _check_dns_ip(self, ip_address: str, available_categories: List[str]) -> Optional[str]:
        """
        Check if the IP address is a known DNS server (using Redis directly, like ASN lookup)
        
        Args:
            ip_address: IP address to check
            available_categories: List of available categories in the model
            
        Returns:
            'DNS' if IP is a known DNS server and DNS category exists, None otherwise
        """
        # Check DNS category is available first
        if 'DNS' not in available_categories:
            return None
        
        # Track whether Redis lookup was attempted and succeeded
        redis_lookup_successful = False
        
        # Attempt Redis lookup only if Redis connection is available
        if self.redis_dns:
            try:
                if self.redis_dns.sismember(REDIS_DNS_KEY, ip_address):
                    logger.debug(f"Detected DNS server from Redis: {ip_address}")
                    return 'DNS'
                # Redis lookup succeeded but IP not found
                redis_lookup_successful = True
            except Exception:
                logger.exception("Error checking DNS server in Redis")
                # Continue to fallback check below
        else:
            logger.debug("Redis DNS connection not available, using fallback only")
        
        # Always check fallback DNS servers (critical infrastructure)
        # This runs when: Redis is None, Redis failed, or Redis didn't find the IP
        fallback_dns_servers = {'8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1'}
        if ip_address in fallback_dns_servers:
            if redis_lookup_successful:
                logger.info(f"Critical DNS server detected via fallback: {ip_address}")
            else:
                logger.warning(f"Using fallback DNS detection (Redis unavailable/failed): {ip_address}")
            return 'DNS'
        
        # Neither Redis nor fallback detected this IP as a DNS server
        return None
    
    def _increment_stats(self, confidence_level: str, prediction_time: float, dns_detected: bool = False, asn_used: bool = False):
        """
        Increment classification statistics counters in Redis (cross-process safe)
        
        Args:
            confidence_level: One of 'HIGH', 'LOW', 'MULTIPLE_CANDIDATES', 'UNCERTAIN'
            prediction_time: Time taken for prediction in seconds
            dns_detected: Whether DNS detection was used
            asn_used: Whether ASN fallback was used
        """
        try:
            # Increment total (shared across all processes via Redis)
            state_manager.increment_classification_stat('total', 1)
            
            # Increment confidence level
            if confidence_level == 'HIGH':
                state_manager.increment_classification_stat('high_confidence', 1)
            elif confidence_level == 'LOW':
                state_manager.increment_classification_stat('low_confidence', 1)
            elif confidence_level == 'MULTIPLE_CANDIDATES':
                state_manager.increment_classification_stat('multiple_candidates', 1)
            elif confidence_level == 'UNCERTAIN':
                state_manager.increment_classification_stat('uncertain', 1)
            
            # Increment detection methods
            if dns_detected:
                state_manager.increment_classification_stat('dns_detections', 1)
            
            if asn_used:
                state_manager.increment_classification_stat('asn_fallback', 1)
            
            # Store prediction time (convert to milliseconds)
            state_manager.add_prediction_time(prediction_time * 1000)
            
        except Exception:
            logger.exception("Error incrementing stats")
    
    def save_classification_stats(self) -> bool:
        """
        Save accumulated statistics from Redis to database and reset counters.
        
        Uses distributed locking to prevent concurrent writes and atomic snapshot-and-reset
        to prevent data loss from TOCTOU race conditions.
        
        Returns:
            bool: True if stats were saved successfully
        """
        # Acquire distributed lock to prevent concurrent persistence (prevents duplication)
        persist_lock = None
        try:
            persist_lock = state_manager.redis_client.lock(
                "classification_stats:persist_lock",
                timeout=30,  # Lock auto-expires after 30 seconds
                blocking_timeout=0  # Non-blocking: fail immediately if lock held
            )
            
            if not persist_lock.acquire(blocking=False):
                logger.debug("Another process is persisting classification stats; skipping this run")
                return False
            
            try:
                # Atomically fetch-and-reset stats (prevents TOCTOU data loss)
                # Use new atomic method if available, fallback to non-atomic for backward compatibility
                if hasattr(state_manager, "snapshot_and_reset_classification_stats"):
                    redis_stats = state_manager.snapshot_and_reset_classification_stats()
                else:
                    logger.warning("Atomic snapshot not available, using non-atomic read-reset (potential data loss)")
                    redis_stats = state_manager.get_classification_stats()
                    # Note: Reset happens later after successful save when using fallback
                
                # Skip if no classifications
                if redis_stats.get('total', 0) == 0:
                    logger.debug("No classifications to save")
                    return False
                
                # Get active model
                active_model_name = self.active_model
                if not active_model_name:
                    logger.warning("No active model, cannot save stats")
                    return False
                
                # Get model configuration
                model_config = ModelConfiguration.objects.get(name=active_model_name)
                
                # Calculate average prediction time
                prediction_times = redis_stats.get('prediction_times', [])
                avg_prediction_time = sum(prediction_times) / len(prediction_times) if prediction_times else 0.0
                
                # Get period start from Redis (or use 5 minutes ago as fallback)
                period_end = timezone.now()
                period_start_key = state_manager.redis_client.get("classification_stats:period_start")
                if period_start_key:
                    from datetime import datetime
                    period_start = datetime.fromisoformat(period_start_key)
                    if not period_start.tzinfo:
                        period_start = timezone.make_aware(period_start)
                else:
                    period_start = period_end - timedelta(minutes=5)
                
                # Create stats record in database
                stats = ClassificationStats.objects.create(
                    model_configuration=model_config,
                    timestamp=period_end,
                    period_start=period_start,
                    period_end=period_end,
                    total_classifications=redis_stats['total'],
                    high_confidence_count=redis_stats['high_confidence'],
                    low_confidence_count=redis_stats['low_confidence'],
                    multiple_candidates_count=redis_stats['multiple_candidates'],
                    uncertain_count=redis_stats['uncertain'],
                    dns_detections=redis_stats['dns_detections'],
                    asn_fallback_count=redis_stats['asn_fallback'],
                    avg_prediction_time_ms=avg_prediction_time
                )
                
                logger.debug(
                    f"Saved classification stats for {active_model_name}: "
                    f"{redis_stats['total']} total, "
                    f"{redis_stats['high_confidence']} high confidence "
                    f"({stats.high_confidence_percentage:.1f}%)"
                )
                
                # Only reset if using non-atomic fallback (atomic method already reset)
                if not hasattr(state_manager, "snapshot_and_reset_classification_stats"):
                    state_manager.reset_classification_stats()
                
                # Store new period start time
                state_manager.redis_client.set("classification_stats:period_start", period_end.isoformat())
                
                return True
                
            finally:
                # Always release lock, even if error occurs
                if persist_lock:
                    try:
                        persist_lock.release()
                    except Exception:
                        logger.exception("Failed to release classification stats persist lock")
            
        except ModelConfiguration.DoesNotExist:
            logger.exception(f"Model configuration '{active_model_name}' not found")
            return False
        except Exception:
            logger.exception("Error saving classification stats")
            return False


# Global model manager instance (lazy-loaded to avoid import-time side effects)
_model_manager = None


def get_model_manager() -> ModelManager:
    """
    Get or create the singleton ModelManager instance.
    
    Lazy initialization avoids heavy side effects (DB/Redis/ML model loading)
    during module import, which can break migrations, tests, and slow startup.
    
    Returns:
        ModelManager: The singleton instance
    """
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


class _ModelManagerProxy:
    """Proxy to provide backward-compatible module-level access"""
    def __getattr__(self, name):
        return getattr(get_model_manager(), name)


# Backward compatibility: expose as module attribute
# Code can use either `model_manager` or `get_model_manager()`
model_manager = _ModelManagerProxy()

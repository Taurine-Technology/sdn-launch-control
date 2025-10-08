import json
import logging
from typing import Any, Dict, Optional
from django.conf import settings
import redis

logger = logging.getLogger(__name__)


class ModelStateManager:
    """Redis-based state manager for fast model state access"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'CHANNEL_REDIS_HOST', 'redis'),
            port=getattr(settings, 'CHANNEL_REDIS_PORT', 6379),
            decode_responses=True
        )
        self.cache_prefix = "model_state:"
        self.cache_ttl = 3600  # 1 hour
    
    def get_active_model(self) -> Optional[str]:
        """Get the currently active model name"""
        try:
            return self.redis_client.get(f"{self.cache_prefix}active_model")
        except Exception as e:
            logger.error(f"Error getting active model from Redis: {e}")
            return None
    
    def set_active_model(self, model_name: str) -> bool:
        """Set the active model name"""
        try:
            self.redis_client.setex(
                f"{self.cache_prefix}active_model",
                self.cache_ttl,
                model_name
            )
            return True
        except Exception as e:
            logger.error(f"Error setting active model in Redis: {e}")
            return False
    
    def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model configuration from Redis cache"""
        try:
            config_json = self.redis_client.get(f"{self.cache_prefix}config:{model_name}")
            if config_json:
                return json.loads(config_json)
            return None
        except Exception as e:
            logger.error(f"Error getting model config from Redis: {e}")
            return None
    
    def set_model_config(self, model_name: str, config: Dict[str, Any]) -> bool:
        """Cache model configuration in Redis"""
        try:
            self.redis_client.setex(
                f"{self.cache_prefix}config:{model_name}",
                self.cache_ttl,
                json.dumps(config)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting model config in Redis: {e}")
            return False
    
    def get_loaded_models(self) -> list:
        """Get list of loaded model names"""
        try:
            loaded_json = self.redis_client.get(f"{self.cache_prefix}loaded_models")
            if loaded_json:
                return json.loads(loaded_json)
            return []
        except Exception as e:
            logger.error(f"Error getting loaded models from Redis: {e}")
            return []
    
    def set_loaded_models(self, model_names: list) -> bool:
        """Set list of loaded model names"""
        try:
            self.redis_client.setex(
                f"{self.cache_prefix}loaded_models",
                self.cache_ttl,
                json.dumps(model_names)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting loaded models in Redis: {e}")
            return False
    
    def add_loaded_model(self, model_name: str) -> bool:
        """Add a model to the loaded models list"""
        try:
            loaded_models = self.get_loaded_models()
            if model_name not in loaded_models:
                loaded_models.append(model_name)
                return self.set_loaded_models(loaded_models)
            return True
        except Exception as e:
            logger.error(f"Error adding loaded model to Redis: {e}")
            return False
    
    def remove_loaded_model(self, model_name: str) -> bool:
        """Remove a model from the loaded models list"""
        try:
            loaded_models = self.get_loaded_models()
            if model_name in loaded_models:
                loaded_models.remove(model_name)
                return self.set_loaded_models(loaded_models)
            return True
        except Exception as e:
            logger.error(f"Error removing loaded model from Redis: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """Clear all model state cache"""
        try:
            keys = self.redis_client.keys(f"{self.cache_prefix}*")
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error clearing model state cache: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Redis is accessible"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    # Classification statistics methods (for cross-process tracking)
    def increment_classification_stat(self, stat_type: str, value: int = 1):
        """Increment a classification statistic counter in Redis"""
        try:
            key = f"classification_stats:{stat_type}"
            self.redis_client.incrby(key, value)
        except Exception as e:
            logger.error(f"Error incrementing classification stat: {e}")
    
    def add_prediction_time(self, time_ms: float):
        """Add a prediction time to the list in Redis"""
        try:
            key = "classification_stats:prediction_times"
            # Store as list with max 1000 entries (rolling window)
            self.redis_client.lpush(key, time_ms)
            self.redis_client.ltrim(key, 0, 999)  # Keep only last 1000
        except Exception as e:
            logger.error(f"Error adding prediction time: {e}")
    
    def get_classification_stats(self) -> dict:
        """Get all classification statistics from Redis"""
        try:
            stats = {
                'total': int(self.redis_client.get("classification_stats:total") or 0),
                'high_confidence': int(self.redis_client.get("classification_stats:high_confidence") or 0),
                'low_confidence': int(self.redis_client.get("classification_stats:low_confidence") or 0),
                'multiple_candidates': int(self.redis_client.get("classification_stats:multiple_candidates") or 0),
                'uncertain': int(self.redis_client.get("classification_stats:uncertain") or 0),
                'dns_detections': int(self.redis_client.get("classification_stats:dns_detections") or 0),
                'asn_fallback': int(self.redis_client.get("classification_stats:asn_fallback") or 0),
            }
            
            # Get prediction times
            times = self.redis_client.lrange("classification_stats:prediction_times", 0, -1)
            stats['prediction_times'] = [float(t) for t in times] if times else []
            
            return stats
        except Exception as e:
            logger.error(f"Error getting classification stats: {e}")
            return {}
    
    def reset_classification_stats(self):
        """Reset all classification statistics counters"""
        try:
            keys = self.redis_client.keys("classification_stats:*")
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Error resetting classification stats: {e}")


# Global state manager instance
state_manager = ModelStateManager()

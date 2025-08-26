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


# Global state manager instance
state_manager = ModelStateManager()

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
        """Clear all model state cache (non-blocking with SCAN)"""
        try:
            # Use SCAN instead of KEYS to avoid blocking Redis
            cursor = 0
            pattern = f"{self.cache_prefix}*"
            while True:
                cursor, keys = self.redis_client.scan(cursor=cursor, match=pattern, count=1000)
                if keys:
                    pipe = self.redis_client.pipeline()
                    for k in keys:
                        pipe.delete(k)
                    pipe.execute()
                if cursor == 0:
                    break
            return True
        except redis.exceptions.RedisError:
            logger.exception("Error clearing model state cache")
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
        except redis.exceptions.RedisError:
            logger.exception("Error incrementing classification stat")
    
    def add_prediction_time(self, time_ms: float):
        """Add a prediction time to the list in Redis (atomic operation)"""
        try:
            key = "classification_stats:prediction_times"
            # Store as list with max 1000 entries (rolling window), atomically
            pipe = self.redis_client.pipeline()
            pipe.lpush(key, time_ms)
            pipe.ltrim(key, 0, 999)  # Keep only last 1000
            pipe.execute()
        except redis.exceptions.RedisError:
            logger.exception("Error adding prediction time")
    
    def get_classification_stats(self) -> dict:
        """Get all classification statistics from Redis (optimized with MGET)"""
        try:
            # Use MGET to fetch all counters in a single network round trip
            keys = [
                "classification_stats:total",
                "classification_stats:high_confidence",
                "classification_stats:low_confidence",
                "classification_stats:multiple_candidates",
                "classification_stats:uncertain",
                "classification_stats:dns_detections",
                "classification_stats:asn_fallback",
            ]
            vals = self.redis_client.mget(keys)
            
            # Map results to dictionary
            stats = dict(zip(
                ['total', 'high_confidence', 'low_confidence', 'multiple_candidates', 
                 'uncertain', 'dns_detections', 'asn_fallback'],
                [int(v or 0) for v in vals]
            ))
            
            # Get prediction times
            times = self.redis_client.lrange("classification_stats:prediction_times", 0, -1)
            stats['prediction_times'] = [float(t) for t in times] if times else []
            
            return stats
        except redis.exceptions.RedisError:
            logger.exception("Error getting classification stats")
            return {}
    
    def reset_classification_stats(self):
        """Reset all classification statistics counters (non-blocking with SCAN)"""
        try:
            # Use SCAN instead of KEYS to avoid blocking Redis
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(
                    cursor=cursor,
                    match="classification_stats:*",
                    count=1000
                )
                if keys:
                    # Use pipeline for efficient batch deletion
                    pipe = self.redis_client.pipeline()
                    for k in keys:
                        pipe.delete(k)
                    pipe.execute()
                if cursor == 0:
                    break
        except redis.exceptions.RedisError:
            logger.exception("Error resetting classification stats")
    
    def snapshot_and_reset_classification_stats(self) -> dict:
        """
        Atomically read counters and reset them using a Lua script to avoid TOCTOU race conditions.
        
        This prevents data loss when new classifications arrive between reading and resetting counters.
        The Lua script executes atomically on the Redis server with no gap between read and delete.
        
        Returns:
            dict: Snapshot of classification statistics before reset
        """
        try:
            # Lua script for atomic read-and-reset
            # All operations execute atomically on Redis server - no TOCTOU race condition
            lua_script = """
            local keys = {
                'classification_stats:total',
                'classification_stats:high_confidence',
                'classification_stats:low_confidence',
                'classification_stats:multiple_candidates',
                'classification_stats:uncertain',
                'classification_stats:dns_detections',
                'classification_stats:asn_fallback'
            }
            local result = {}
            
            -- Read all counter values
            for i, k in ipairs(keys) do
                local v = redis.call('GET', k)
                result[i] = tonumber(v) or 0
            end
            
            -- Read prediction_times list (capped list, snapshot all entries)
            local times = redis.call('LRANGE', 'classification_stats:prediction_times', 0, -1)
            
            -- Reset phase: delete all counters and the list
            for _, k in ipairs(keys) do
                redis.call('DEL', k)
            end
            redis.call('DEL', 'classification_stats:prediction_times')
            
            -- Return snapshot [counters..., times]
            return {result[1], result[2], result[3], result[4], result[5], result[6], result[7], times}
            """
            
            # Register and execute Lua script
            fn = self.redis_client.register_script(lua_script)
            data = fn()
            
            # Parse results from Lua script
            return {
                'total': int(data[0]),
                'high_confidence': int(data[1]),
                'low_confidence': int(data[2]),
                'multiple_candidates': int(data[3]),
                'uncertain': int(data[4]),
                'dns_detections': int(data[5]),
                'asn_fallback': int(data[6]),
                'prediction_times': [float(x) for x in data[7]] if data[7] else [],
            }
            
        except redis.exceptions.RedisError:
            logger.exception("Error in atomic snapshot and reset of classification stats")
            # Fallback to non-atomic read if Lua script fails
            logger.warning("Falling back to non-atomic read-reset (potential data loss)")
            stats = self.get_classification_stats()
            self.reset_classification_stats()
            return stats


# Global state manager instance
state_manager = ModelStateManager()

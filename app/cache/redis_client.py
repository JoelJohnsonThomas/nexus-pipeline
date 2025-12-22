"""
Redis client for caching and message queue.
Provides caching layer for API responses and frequently accessed data.
"""
import redis
import json
import os
from typing import Optional, Any, List
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for caching and data storage"""
    
    def __init__(self, host: str = None, port: int = None, db: int = 0):
        """
        Initialize Redis client.
        
        Args:
            host: Redis host (default: from env or 'localhost')
            port: Redis port (default: from env or 6379)
            db: Redis database number (default: 0)
        """
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = int(port or os.getenv('REDIS_PORT', 6379))
        self.db = db
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Cache key
            value: Value to store (will be JSON serialized if dict/list)
            ttl: Time to live in seconds (optional)
        
        Returns:
            True if successful
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get a value from Redis.
        
        Args:
            key: Cache key
            deserialize: Attempt to deserialize JSON (default: True)
        
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            
            if value is None:
                return None
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            *keys: Keys to delete
        
        Returns:
            Number of keys deleted
        """
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key"""
        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Error setting expiration: {e}")
            return False
    
    def get_many(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple values at once"""
        try:
            values = self.client.mget(keys)
            result = []
            for value in values:
                if value:
                    try:
                        result.append(json.loads(value))
                    except json.JSONDecodeError:
                        result.append(value)
                else:
                    result.append(None)
            return result
        except Exception as e:
            logger.error(f"Error getting multiple keys: {e}")
            return [None] * len(keys)
    
    def cache_articles(self, cache_key: str, articles: List[dict], ttl: int = 3600) -> bool:
        """
        Cache a list of articles.
        
        Args:
            cache_key: Unique cache key
            articles: List of article dictionaries
            ttl: Time to live in seconds (default: 1 hour)
        
        Returns:
            True if successful
        """
        return self.set(cache_key, articles, ttl)
    
    def get_cached_articles(self, cache_key: str) -> Optional[List[dict]]:
        """
        Retrieve cached articles.
        
        Args:
            cache_key: Cache key
        
        Returns:
            List of article dictionaries or None
        """
        return self.get(cache_key)
    
    def flush_all(self) -> bool:
        """Clear all cached data (use with caution!)"""
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get Redis statistics"""
        try:
            info = self.client.info()
            return {
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


# Global Redis client instance
_redis_client = None


def get_redis_client() -> RedisClient:
    """Get global Redis client instance (singleton pattern)"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client

"""
Redis Cache Connection

Provides Redis client for caching, rate limiting, and session storage.
"""

from redis.asyncio import Redis
from typing import Optional
import os
import json


# Redis connection configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Global Redis client
_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get or create the Redis client instance.
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = await Redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        
        # Verify connectivity
        await _redis_client.ping()
        print(f"✅ Redis connected: {REDIS_URL}")
    
    return _redis_client


async def close_redis():
    """
    Close Redis connection on application shutdown.
    """
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.close()
        print("✅ Redis connections closed")
        _redis_client = None


class RedisCache:
    """
    Helper class for common Redis caching operations.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL in seconds."""
        await self.redis.setex(key, ttl, value)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set_json(self, key: str, value: dict, ttl: int = 3600):
        """Set JSON value in cache with TTL."""
        await self.redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        """Delete key from cache."""
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.redis.exists(key) > 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        return await self.redis.incrby(key, amount)
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        return await self.redis.decrby(key, amount)
    
    async def expire(self, key: str, ttl: int):
        """Set expiration on existing key."""
        await self.redis.expire(key, ttl)
    
    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key."""
        return await self.redis.ttl(key)

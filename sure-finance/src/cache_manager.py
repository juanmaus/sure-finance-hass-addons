"""Cache management for Sure Finance addon.

This module handles caching of API responses and calculated data
to reduce API calls and improve performance.
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for the addon."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600
    ):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory for file-based cache
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = cache_dir or Path("/data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.redis_url = redis_url
        self._redis: Optional[Redis] = None
        self.default_ttl = default_ttl
        
        # In-memory cache for frequently accessed data
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
    async def connect_redis(self):
        """Connect to Redis if URL provided."""
        if self.redis_url and not self._redis:
            try:
                # redis.asyncio client (Python 3.11 compatible)
                self._redis = Redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection lazily with a ping
                try:
                    await self._redis.ping()
                except Exception:
                    pass
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self._redis = None
                
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            
    def _get_cache_key(self, key: str, namespace: str = "default") -> str:
        """Generate cache key with namespace.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Full cache key
        """
        return f"sure_finance:{namespace}:{key}"
        
    async def get(
        self,
        key: str,
        namespace: str = "default"
    ) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Cached value or None
        """
        full_key = self._get_cache_key(key, namespace)
        
        # Check memory cache first
        if full_key in self._memory_cache:
            entry = self._memory_cache[full_key]
            if datetime.utcnow() < entry["expires_at"]:
                logger.debug(f"Memory cache hit: {full_key}")
                return entry["value"]
            else:
                del self._memory_cache[full_key]
                
        # Check Redis if available
        if self._redis:
            try:
                value = await self._redis.get(full_key)
                if value:
                    logger.debug(f"Redis cache hit: {full_key}")
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                
        # Check file cache
        cache_file = self.cache_dir / f"{full_key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    if datetime.utcnow() < data["expires_at"]:
                        logger.debug(f"File cache hit: {full_key}")
                        return data["value"]
                    else:
                        cache_file.unlink()
            except Exception as e:
                logger.error(f"File cache read error: {e}")
                
        logger.debug(f"Cache miss: {full_key}")
        return None
        
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ):
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            namespace: Cache namespace
        """
        full_key = self._get_cache_key(key, namespace)
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        # Store in memory cache
        self._memory_cache[full_key] = {
            "value": value,
            "expires_at": expires_at
        }
        
        # Store in Redis if available
        if self._redis:
            try:
                await self._redis.setex(
                    full_key,
                    ttl,
                    json.dumps(value, default=str)
                )
                logger.debug(f"Cached to Redis: {full_key}")
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                
        # Store in file cache
        try:
            cache_file = self.cache_dir / f"{full_key}.cache"
            with open(cache_file, "wb") as f:
                pickle.dump({
                    "value": value,
                    "expires_at": expires_at
                }, f)
            logger.debug(f"Cached to file: {full_key}")
        except Exception as e:
            logger.error(f"File cache write error: {e}")
            
    async def delete(
        self,
        key: str,
        namespace: str = "default"
    ):
        """Delete value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
        """
        full_key = self._get_cache_key(key, namespace)
        
        # Remove from memory cache
        self._memory_cache.pop(full_key, None)
        
        # Remove from Redis
        if self._redis:
            try:
                await self._redis.delete(full_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                
        # Remove from file cache
        cache_file = self.cache_dir / f"{full_key}.cache"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"File cache delete error: {e}")
                
    async def clear_namespace(
        self,
        namespace: str
    ):
        """Clear all cache entries in a namespace.
        
        Args:
            namespace: Cache namespace to clear
        """
        prefix = f"sure_finance:{namespace}:"
        
        # Clear memory cache
        keys_to_delete = [
            k for k in self._memory_cache.keys()
            if k.startswith(prefix)
        ]
        for key in keys_to_delete:
            del self._memory_cache[key]
            
        # Clear Redis
        if self._redis:
            try:
                async for key in self._redis.scan_iter(match=f"{prefix}*"):
                    await self._redis.delete(key)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
                
        # Clear file cache
        for cache_file in self.cache_dir.glob(f"{prefix}*.cache"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"File cache clear error: {e}")
                
    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> Any:
        """Get from cache or compute and cache.
        
        Args:
            key: Cache key
            factory: Async function to compute value
            ttl: Time-to-live in seconds
            namespace: Cache namespace
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = await self.get(key, namespace)
        if value is not None:
            return value
            
        # Compute value
        value = await factory()
        
        # Cache the result
        await self.set(key, value, ttl, namespace)
        
        return value
        
    def cleanup_expired(self):
        """Clean up expired entries from memory and file cache."""
        now = datetime.utcnow()
        
        # Clean memory cache
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if now >= v["expires_at"]
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            
        # Clean file cache
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    if now >= data["expires_at"]:
                        cache_file.unlink()
            except Exception as e:
                logger.error(f"Cleanup error for {cache_file}: {e}")
                # Delete corrupted cache file
                try:
                    cache_file.unlink()
                except:
                    pass
                    
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
    # Cache key generators for common data types
    def account_key(self, account_id: Optional[str] = None) -> str:
        """Generate cache key for account data."""
        if account_id:
            return f"account:{account_id}"
        return "accounts:all"
        
    def transaction_key(
        self,
        account_id: Optional[str] = None,
        page: Optional[int] = None
    ) -> str:
        """Generate cache key for transaction data."""
        parts = ["transactions"]
        if account_id:
            parts.append(f"account:{account_id}")
        if page:
            parts.append(f"page:{page}")
        return ":".join(parts)
        
    def summary_key(self, period: Optional[str] = None) -> str:
        """Generate cache key for financial summary."""
        if period:
            return f"summary:{period}"
        return "summary:current"
        
    def cashflow_key(self, year: int, month: int) -> str:
        """Generate cache key for monthly cashflow."""
        return f"cashflow:{year:04d}-{month:02d}"
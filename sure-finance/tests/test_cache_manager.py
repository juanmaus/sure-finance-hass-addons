"""Tests for cache manager."""

import asyncio
import json
import pickle
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.cache_manager import CacheManager


@pytest.fixture
async def cache_manager(tmp_path):
    """Create cache manager instance."""
    manager = CacheManager(
        cache_dir=tmp_path / "cache",
        default_ttl=3600
    )
    yield manager
    await manager.close()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock()
    mock.delete = AsyncMock()
    mock.scan_iter = AsyncMock(return_value=[])
    return mock


class TestCacheManager:
    """Test cache manager."""
    
    @pytest.mark.asyncio
    async def test_init(self, tmp_path):
        """Test initialization."""
        cache_dir = tmp_path / "test_cache"
        manager = CacheManager(
            cache_dir=cache_dir,
            redis_url="redis://localhost:6379",
            default_ttl=7200
        )
        
        assert manager.cache_dir == cache_dir
        assert cache_dir.exists()
        assert manager.redis_url == "redis://localhost:6379"
        assert manager.default_ttl == 7200
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_memory_cache_set_get(self, cache_manager):
        """Test memory cache operations."""
        # Set value
        await cache_manager.set("test_key", {"data": "value"}, ttl=60)
        
        # Get value
        result = await cache_manager.get("test_key")
        assert result == {"data": "value"}
        
        # Check memory cache directly
        full_key = cache_manager._get_cache_key("test_key")
        assert full_key in cache_manager._memory_cache
    
    @pytest.mark.asyncio
    async def test_file_cache(self, cache_manager):
        """Test file cache operations."""
        data = {"test": "data", "number": 42}
        
        # Set value
        await cache_manager.set("file_test", data, ttl=60)
        
        # Clear memory cache to force file read
        cache_manager._memory_cache.clear()
        
        # Get value from file
        result = await cache_manager.get("file_test")
        assert result == data
        
        # Check file exists
        cache_file = cache_manager.cache_dir / "sure_finance:default:file_test.cache"
        assert cache_file.exists()
    
    @pytest.mark.asyncio
    async def test_redis_cache(self, cache_manager, mock_redis):
        """Test Redis cache operations."""
        cache_manager._redis = mock_redis
        
        # Test set
        await cache_manager.set("redis_test", {"data": "value"}, ttl=60)
        mock_redis.setex.assert_called_once()
        
        # Test get
        mock_redis.get.return_value = json.dumps({"data": "value"})
        cache_manager._memory_cache.clear()  # Force Redis read
        
        result = await cache_manager.get("redis_test")
        assert result == {"data": "value"}
        mock_redis.get.assert_called()
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """Test cache expiration."""
        # Set with very short TTL
        await cache_manager.set("expire_test", "value", ttl=0)
        
        # Wait a moment
        await asyncio.sleep(0.1)
        
        # Should be expired
        result = await cache_manager.get("expire_test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_manager, mock_redis):
        """Test cache deletion."""
        cache_manager._redis = mock_redis
        
        # Set value
        await cache_manager.set("delete_test", "value")
        
        # Delete
        await cache_manager.delete("delete_test")
        
        # Check deleted from memory
        full_key = cache_manager._get_cache_key("delete_test")
        assert full_key not in cache_manager._memory_cache
        
        # Check Redis delete called
        mock_redis.delete.assert_called_once()
        
        # Check file deleted
        cache_file = cache_manager.cache_dir / f"{full_key}.cache"
        assert not cache_file.exists()
    
    @pytest.mark.asyncio
    async def test_clear_namespace(self, cache_manager, mock_redis):
        """Test clearing namespace."""
        cache_manager._redis = mock_redis
        
        # Set values in different namespaces
        await cache_manager.set("key1", "value1", namespace="test_ns")
        await cache_manager.set("key2", "value2", namespace="test_ns")
        await cache_manager.set("key3", "value3", namespace="other_ns")
        
        # Clear test_ns
        await cache_manager.clear_namespace("test_ns")
        
        # Check test_ns cleared
        assert await cache_manager.get("key1", namespace="test_ns") is None
        assert await cache_manager.get("key2", namespace="test_ns") is None
        
        # Check other_ns not affected
        assert await cache_manager.get("key3", namespace="other_ns") == "value3"
    
    @pytest.mark.asyncio
    async def test_get_or_set(self, cache_manager):
        """Test get_or_set functionality."""
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            return {"computed": "value", "count": call_count}
        
        # First call - should compute
        result1 = await cache_manager.get_or_set("compute_test", factory)
        assert result1 == {"computed": "value", "count": 1}
        assert call_count == 1
        
        # Second call - should use cache
        result2 = await cache_manager.get_or_set("compute_test", factory)
        assert result2 == {"computed": "value", "count": 1}
        assert call_count == 1  # Factory not called again
    
    def test_cache_key_generators(self, cache_manager):
        """Test cache key generation methods."""
        # Account key
        assert cache_manager.account_key() == "accounts:all"
        assert cache_manager.account_key("123") == "account:123"
        
        # Transaction key
        assert cache_manager.transaction_key() == "transactions"
        assert cache_manager.transaction_key(account_id="456") == "transactions:account:456"
        assert cache_manager.transaction_key(page=2) == "transactions:page:2"
        assert cache_manager.transaction_key("456", 2) == "transactions:account:456:page:2"
        
        # Summary key
        assert cache_manager.summary_key() == "summary:current"
        assert cache_manager.summary_key("2024-01") == "summary:2024-01"
        
        # Cashflow key
        assert cache_manager.cashflow_key(2024, 1) == "cashflow:2024-01"
        assert cache_manager.cashflow_key(2024, 12) == "cashflow:2024-12"
    
    def test_cleanup_expired(self, cache_manager):
        """Test cleanup of expired entries."""
        # Add expired entry to memory cache
        expired_time = datetime.utcnow() - timedelta(hours=1)
        cache_manager._memory_cache["expired_key"] = {
            "value": "old",
            "expires_at": expired_time
        }
        
        # Add valid entry
        valid_time = datetime.utcnow() + timedelta(hours=1)
        cache_manager._memory_cache["valid_key"] = {
            "value": "new",
            "expires_at": valid_time
        }
        
        # Run cleanup
        cache_manager.cleanup_expired()
        
        # Check results
        assert "expired_key" not in cache_manager._memory_cache
        assert "valid_key" in cache_manager._memory_cache
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, cache_manager):
        """Test handling of Redis connection failure."""
        with patch("redis.asyncio.Redis.from_url", side_effect=Exception("Connection failed")):
            await cache_manager.connect_redis()
            assert cache_manager._redis is None
        
        # Should still work with file cache
        await cache_manager.set("fallback_test", "value")
        result = await cache_manager.get("fallback_test")
        assert result == "value"
    
    @pytest.mark.asyncio
    async def test_corrupted_file_cache(self, cache_manager):
        """Test handling of corrupted cache files."""
        # Create corrupted cache file
        cache_file = cache_manager.cache_dir / "sure_finance:default:corrupt.cache"
        cache_file.write_text("corrupted data")
        
        # Should return None and delete corrupted file
        result = await cache_manager.get("corrupt")
        assert result is None
        assert not cache_file.exists()
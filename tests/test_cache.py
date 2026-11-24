import pytest
from src.cache.redis_cache import RedisCache

def test_redis_cache_graceful_degradation_when_offline():
    # Attempt connecting to a non-existent Redis port to test graceful offline fallback
    cache = RedisCache(redis_url="redis://localhost:9999/0", enabled=True)
    assert cache.available is False
    
    # Operations must degrade silently without crashing
    hit = cache.get("Sample test question?")
    assert hit is None
    
    saved = cache.set("Sample test question?", {"grounded": True, "final_response": "Test"})
    assert saved is False

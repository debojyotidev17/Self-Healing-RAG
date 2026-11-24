import json
import hashlib
import logging
from typing import Optional, Dict, Any
from src.config import REDIS_URL, CACHE_ENABLED, CACHE_TTL

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Semantic/Exact query caching layer with Redis.
    Features Graceful Degradation: If Redis server is offline or unreachable,
    the system logs a warning and degrades gracefully without failing any requests.
    """
    def __init__(self, redis_url: str = REDIS_URL, enabled: bool = CACHE_ENABLED, ttl: int = CACHE_TTL):
        self.enabled = enabled
        self.ttl = ttl
        self.redis_client = None
        self.available = False

        if self.enabled:
            try:
                import redis
                self.redis_client = redis.Redis.from_url(redis_url, socket_connect_timeout=1.0)
                # Ping test
                self.redis_client.ping()
                self.available = True
                logger.info(f"Connected to Redis cache at {redis_url}")
            except Exception as e:
                logger.warning(f"Redis cache unavailable ({e}). Operating in cache-bypass mode.")
                self.available = False

    def _make_key(self, query: str) -> str:
        """Generates deterministic cache key from normalized query string."""
        normalized = query.strip().lower()
        query_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"rag_cache:{query_hash}"

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result dictionary for a query. Returns None if cache miss or unavailable."""
        if not self.enabled or not self.available or not self.redis_client:
            return None

        try:
            key = self._make_key(query)
            data = self.redis_client.get(key)
            if data:
                logger.info(f"Cache HIT for query: '{query[:50]}'")
                return json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Redis cache get failed ({e}). Bypassing cache.")
            
        return None

    def set(self, query: str, response_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache response data for a query. Returns True if successful."""
        if not self.enabled or not self.available or not self.redis_client:
            return False

        # Only cache grounded responses
        if not response_data.get("grounded", False) or response_data.get("fallback", False):
            return False

        try:
            key = self._make_key(query)
            effective_ttl = ttl if ttl is not None else self.ttl
            payload = json.dumps(response_data)
            self.redis_client.setex(key, effective_ttl, payload)
            logger.info(f"Cached grounded response for query: '{query[:50]}'")
            return True
        except Exception as e:
            logger.warning(f"Redis cache set failed ({e}).")
            return False

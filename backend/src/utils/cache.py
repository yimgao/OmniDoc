"""
Redis-based caching utilities for OmniDoc
"""
import json
import logging
import os
from typing import Any, Optional, Dict
import redis
from functools import wraps

logger = logging.getLogger(__name__)

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Redis client (with connection pooling)
try:
    # For Upstash Redis, we need SSL support
    test_url = REDIS_URL
    
    if "upstash.io" in REDIS_URL:
        # Upstash requires SSL, convert redis:// to rediss://
        if not REDIS_URL.startswith("rediss://"):
            test_url = REDIS_URL.replace("redis://", "rediss://", 1)
    
    # rediss:// automatically enables SSL, no need to pass ssl parameter
    redis_client = redis.from_url(
        test_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Redis connection failed: {type(e).__name__}: {str(e)}")
    REDIS_AVAILABLE = False
    redis_client = None


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments"""
    key_parts = [prefix]
    if args:
        key_parts.extend(str(arg) for arg in args)
    if kwargs:
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def cache_result(ttl: int = 3600, key_prefix: str = "cache"):
    """
    Decorator to cache function results in Redis
    Supports both sync and async functions
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Prefix for cache keys
    """
    def decorator(func):
        import asyncio
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not REDIS_AVAILABLE:
                    return await func(*args, **kwargs)
                
                cache_key = get_cache_key(key_prefix, func.__name__, *args, **kwargs)
                
                # Try to get from cache
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        return json.loads(cached)
                except Exception:
                    pass
                
                # Call function and cache result
                result = await func(*args, **kwargs)
                
                # Store in cache
                try:
                    redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                except Exception:
                    pass
                
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not REDIS_AVAILABLE:
                    return func(*args, **kwargs)
                
                cache_key = get_cache_key(key_prefix, func.__name__, *args, **kwargs)
                
                # Try to get from cache
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        return json.loads(cached)
                except Exception:
                    pass
                
                # Call function and cache result
                result = func(*args, **kwargs)
                
                # Store in cache
                try:
                    redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                except Exception:
                    pass
                
                return result
            return sync_wrapper
    return decorator


def get_cached(key: str) -> Optional[Any]:
    """Get a value from cache"""
    if not REDIS_AVAILABLE:
        return None
    
    try:
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    
    return None


def set_cached(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set a value in cache"""
    if not REDIS_AVAILABLE:
        return False
    
    try:
        redis_client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception:
        return False


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache keys matching a pattern"""
    if not REDIS_AVAILABLE:
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception:
        return 0


def cache_document_templates(ttl: int = 86400) -> callable:
    """Cache document templates (cache for 24 hours by default)"""
    return cache_result(ttl=ttl, key_prefix="doc_templates")


def cache_project_results(project_id: str, ttl: int = 3600) -> callable:
    """Cache project results (cache for 1 hour by default)"""
    return cache_result(ttl=ttl, key_prefix=f"project:{project_id}")


def cache_llm_response(ttl: int = 3600):
    """
    Decorator to cache LLM responses in Redis.
    
    This decorator caches LLM API responses to reduce API calls and costs.
    Cache key is generated from function name, prompt, model, and temperature.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
    
    Usage:
        @cache_llm_response(ttl=3600)
        def generate_text(prompt: str, model: str = "default", temperature: float = 0.7):
            # LLM call
            return response
    """
    import hashlib
    
    def decorator(func):
        import asyncio
        is_async = asyncio.iscoroutinefunction(func)
        
        def _generate_cache_key(prompt: str, model: Optional[str] = None, 
                               temperature: Optional[float] = None, **kwargs) -> str:
            """Generate a cache key from LLM call parameters"""
            # Create a hash of the prompt and parameters
            key_parts = [
                "llm",
                func.__name__,
                prompt[:200],  # First 200 chars of prompt
                model or "default",
                str(temperature) if temperature is not None else "default",
            ]
            # Add sorted kwargs for consistent hashing
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
            
            key_string = ":".join(str(p) for p in key_parts)
            # Use hash for very long prompts
            if len(key_string) > 200:
                key_hash = hashlib.md5(key_string.encode()).hexdigest()
                return f"llm:{func.__name__}:{key_hash}"
            return f"llm:{func.__name__}:{key_string}"
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not REDIS_AVAILABLE:
                    return await func(*args, **kwargs)
                
                # Extract prompt and model from args/kwargs
                prompt = args[0] if args else kwargs.get("prompt", "")
                model = kwargs.get("model") or (args[1] if len(args) > 1 else None)
                temperature = kwargs.get("temperature") or (args[2] if len(args) > 2 else None)
                
                cache_key = _generate_cache_key(prompt, model, temperature, **kwargs)
                
                # Try to get from cache
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        logger = logging.getLogger(__name__)
                        logger.debug(f"✅ LLM cache hit for {func.__name__}")
                        return json.loads(cached)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Cache read error: {e}")
                
                # Call function and cache result
                result = await func(*args, **kwargs)
                
                # Store in cache
                try:
                    redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                    logger = logging.getLogger(__name__)
                    logger.debug(f"✅ LLM response cached for {func.__name__}")
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Cache write error: {e}")
                
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not REDIS_AVAILABLE:
                    return func(*args, **kwargs)
                
                # Extract prompt and model from args/kwargs
                prompt = args[0] if args else kwargs.get("prompt", "")
                model = kwargs.get("model") or (args[1] if len(args) > 1 else None)
                temperature = kwargs.get("temperature") or (args[2] if len(args) > 2 else None)
                
                cache_key = _generate_cache_key(prompt, model, temperature, **kwargs)
                
                # Try to get from cache
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        logger = logging.getLogger(__name__)
                        logger.debug(f"✅ LLM cache hit for {func.__name__}")
                        return json.loads(cached)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Cache read error: {e}")
                
                # Call function and cache result
                result = func(*args, **kwargs)
                
                # Store in cache
                try:
                    redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                    logger = logging.getLogger(__name__)
                    logger.debug(f"✅ LLM response cached for {func.__name__}")
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Cache write error: {e}")
                
                return result
            return sync_wrapper
    return decorator


"""
Redis client utilities with connection pooling and rate limiting.

This module provides:
- Connection pooling for Redis clients
- Rate limiting to respect monthly request limits
- Automatic fallback mechanisms when Redis is unavailable
- Metrics tracking for Redis usage
"""
from __future__ import annotations

import os
import ssl
import time
import threading
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timedelta
from collections import defaultdict
import redis
import redis.asyncio as redis_async

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RedisRateLimiter:
    """
    Rate limiter for Redis operations to respect monthly request limits.
    
    Tracks requests per hour/day/month and throttles when approaching limits.
    Falls back gracefully when limits are reached.
    """
    
    def __init__(
        self,
        max_requests_per_hour: int = 1000,
        max_requests_per_day: int = 10000,
        max_requests_per_month: int = 100000,
        warning_threshold: float = 0.8,  # Warn at 80% of limit
    ):
        self.max_requests_per_hour = max_requests_per_hour
        self.max_requests_per_day = max_requests_per_day
        self.max_requests_per_month = max_requests_per_month
        self.warning_threshold = warning_threshold
        
        self.request_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = threading.Lock()
        self.monthly_reset_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    
    def _get_period_keys(self) -> Dict[str, str]:
        """Get keys for current hour, day, and month periods"""
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")
        
        # Reset monthly counter if new month
        if now.month != self.monthly_reset_date.month or now.year != self.monthly_reset_date.year:
            with self._lock:
                self.monthly_reset_date = now.replace(day=1, hour=0, minute=0, second=0)
                # Clear old monthly data
                for key in list(self.request_counts.keys()):
                    if not key.startswith(month_key):
                        del self.request_counts[key]
        
        return {
            "hour": hour_key,
            "day": day_key,
            "month": month_key
        }
    
    def can_make_request(self) -> tuple[bool, Optional[str]]:
        """
        Check if we can make a Redis request without exceeding limits.
        
        Returns:
            Tuple of (can_make_request: bool, error_message: Optional[str])
        """
        with self._lock:
            keys = self._get_period_keys()
            counts = self.request_counts
            
            hour_count = counts.get(keys["hour"], {}).get("count", 0)
            day_count = counts.get(keys["day"], {}).get("count", 0)
            month_count = sum(
                v.get("count", 0) for k, v in counts.items()
                if k.startswith(keys["month"].split("-")[0])  # All keys for this month
            )
            
            # Check limits
            if hour_count >= self.max_requests_per_hour:
                return False, f"Hourly limit reached: {hour_count}/{self.max_requests_per_hour}"
            if day_count >= self.max_requests_per_day:
                return False, f"Daily limit reached: {day_count}/{self.max_requests_per_day}"
            if month_count >= self.max_requests_per_month:
                return False, f"Monthly limit reached: {month_count}/{self.max_requests_per_month}"
            
            # Check warning thresholds
            if hour_count >= self.max_requests_per_hour * self.warning_threshold:
                logger.warning(
                    f"⚠️ Redis hourly limit approaching: {hour_count}/{self.max_requests_per_hour} "
                    f"({hour_count/self.max_requests_per_hour*100:.1f}%)"
                )
            
            return True, None
    
    def record_request(self) -> None:
        """Record a Redis request"""
        with self._lock:
            keys = self._get_period_keys()
            for period, key in keys.items():
                if key not in self.request_counts:
                    self.request_counts[key] = {"count": 0, "first_request": time.time()}
                self.request_counts[key]["count"] += 1
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        with self._lock:
            keys = self._get_period_keys()
            return {
                "hour": {
                    "count": self.request_counts.get(keys["hour"], {}).get("count", 0),
                    "limit": self.max_requests_per_hour,
                    "percentage": (self.request_counts.get(keys["hour"], {}).get("count", 0) / self.max_requests_per_hour) * 100
                },
                "day": {
                    "count": sum(
                        v.get("count", 0) for k, v in self.request_counts.items()
                        if k.startswith(keys["day"])
                    ),
                    "limit": self.max_requests_per_day,
                },
                "month": {
                    "count": sum(
                        v.get("count", 0) for k, v in self.request_counts.items()
                        if k.startswith(keys["month"].split("-")[0])
                    ),
                    "limit": self.max_requests_per_month,
                }
            }


# Global rate limiter instance
_redis_rate_limiter: Optional[RedisRateLimiter] = None


def get_redis_rate_limiter() -> RedisRateLimiter:
    """Get or create global Redis rate limiter"""
    global _redis_rate_limiter
    if _redis_rate_limiter is None:
        # Get limits from environment or use defaults
        _redis_rate_limiter = RedisRateLimiter(
            max_requests_per_hour=int(os.getenv("REDIS_MAX_REQUESTS_PER_HOUR", "1000")),
            max_requests_per_day=int(os.getenv("REDIS_MAX_REQUESTS_PER_DAY", "10000")),
            max_requests_per_month=int(os.getenv("REDIS_MAX_REQUESTS_PER_MONTH", "100000")),
        )
    return _redis_rate_limiter


class RedisClientPool:
    """
    Redis client pool with connection reuse and rate limiting.
    
    Manages a pool of Redis connections to minimize overhead and respect rate limits.
    """
    
    def __init__(self, redis_url: str, max_connections: int = 5, use_ssl: bool = False):
        """
        Initialize Redis client pool.
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool (default 5, reduced for Upstash compatibility)
            use_ssl: Whether to use SSL/TLS
        """
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.use_ssl = use_ssl
        
        parsed_url = urlparse(redis_url)
        self.connection_params = {
            "host": parsed_url.hostname,
            "port": parsed_url.port or 6379,
            "password": parsed_url.password,
            "decode_responses": False,  # Celery needs bytes
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
        }
        
        if use_ssl:
            self.connection_params.update({
                "ssl": True,
                "ssl_cert_reqs": ssl.CERT_NONE,
            })
        
        self._sync_pool: Optional[redis.ConnectionPool] = None
        self._sync_client: Optional[redis.Redis] = None  # Single reusable client instance
        self._async_client: Optional[redis_async.Redis] = None
        self._rate_limiter = get_redis_rate_limiter()
        self._lock = threading.Lock()
    
    def get_sync_client(self) -> redis.Redis:
        """
        Get a synchronous Redis client from pool (reused singleton).
        
        Uses a single client instance with connection pooling to avoid
        connection exhaustion issues with Upstash Redis.
        """
        if self._sync_client is None:
            with self._lock:
                if self._sync_client is None:
                    # Reduced max_connections for Upstash compatibility
                    # Also add connection retry settings
                    self._sync_pool = redis.ConnectionPool(
                        max_connections=self.max_connections,
                        retry_on_timeout=True,
                        health_check_interval=30,
                        **self.connection_params
                    )
                    # Create a single reusable client instance
                    self._sync_client = redis.Redis(connection_pool=self._sync_pool)
        
        return self._sync_client
    
    async def get_async_client(self) -> redis_async.Redis:
        """Get an async Redis client"""
        if self._async_client is None:
            parsed_url = urlparse(self.redis_url)
            async_params = {
                "host": parsed_url.hostname,
                "port": parsed_url.port or 6379,
                "password": parsed_url.password,
                "decode_responses": True,
                "ssl_cert_reqs": ssl.CERT_NONE if self.use_ssl else None,
            }
            if self.use_ssl:
                async_params["ssl"] = True
            
            self._async_client = redis_async.from_url(
                self.redis_url.replace("redis://", "rediss://") if self.use_ssl and not self.redis_url.startswith("rediss://") else self.redis_url,
                decode_responses=True,
                **{k: v for k, v in async_params.items() if k != "host" and k != "port" and k != "password"}
            )
        
        return self._async_client
    
    def check_rate_limit(self) -> tuple[bool, Optional[str]]:
        """Check if we can make a request within rate limits"""
        return self._rate_limiter.can_make_request()
    
    def record_request(self) -> None:
        """Record a Redis request"""
        self._rate_limiter.record_request()
    
    def safe_publish(
        self,
        channel: str,
        message: str,
        fallback_func: Optional[Any] = None
    ) -> bool:
        """
        Safely publish to Redis channel with rate limiting and fallback.
        
        Args:
            channel: Redis channel name
            message: Message to publish (will be JSON encoded if needed)
            fallback_func: Optional function to call if Redis fails
        
        Returns:
            True if published successfully, False otherwise
        """
        # Check rate limit
        can_make, error_msg = self.check_rate_limit()
        if not can_make:
            logger.warning(f"⚠️ Redis rate limit reached: {error_msg}. Using fallback.")
            if fallback_func:
                try:
                    fallback_func()
                except Exception as e:
                    logger.error(f"Fallback function failed: {e}")
            return False
        
        try:
            client = self.get_sync_client()
            
            # Ensure message is bytes for Redis
            if isinstance(message, str):
                import json
                message = json.dumps(message) if not message.startswith("{") else message
                message = message.encode('utf-8')
            
            # Try to publish with connection retry
            try:
                client.publish(channel, message)
                self.record_request()
                return True
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError, OSError) as conn_err:
                error_str = str(conn_err).lower()
                if "too many connections" in error_str or "connection" in error_str:
                    logger.warning(
                        f"Redis connection pool exhausted. "
                        f"Pool size: {self.max_connections}, Active: {self._sync_pool.created_connections if self._sync_pool else 'unknown'}. "
                        f"Using fallback."
                    )
                    if fallback_func:
                        try:
                            fallback_func()
                        except Exception as e:
                            logger.error(f"Fallback function failed: {e}")
                    return False
                raise
        
        except redis.exceptions.ResponseError as e:
            error_str = str(e).lower()
            if "max requests limit exceeded" in error_str:
                logger.error(f"❌ Redis monthly limit exceeded. Using fallback.")
                if fallback_func:
                    try:
                        fallback_func()
                    except Exception as e:
                        logger.error(f"Fallback function failed: {e}")
                return False
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "too many connections" in error_str:
                logger.warning(
                    f"Redis connection pool exhausted: {e}. "
                    f"Consider reducing concurrent operations or increasing pool size. Using fallback."
                )
            else:
                logger.error(f"Redis publish failed: {e}. Using fallback.")
            if fallback_func:
                try:
                    fallback_func()
                except Exception as e2:
                    logger.error(f"Fallback function failed: {e2}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get Redis usage statistics"""
        return self._rate_limiter.get_usage_stats()
    
    def get_pool_health(self) -> Dict[str, Any]:
        """
        Get Redis connection pool health metrics.
        
        Returns:
            Dictionary with pool health information including:
            - pool_size: Maximum connections in pool
            - created_connections: Number of connections created (if available)
            - health_status: "healthy", "warning", "critical", or "unknown"
            - pool_initialized: Whether pool is initialized
            - usage_stats: Rate limiting usage statistics
            - rate_limit_ok: Whether rate limit check passes
        """
        health = {
            "pool_size": self.max_connections,
            "pool_initialized": self._sync_pool is not None,
            "health_status": "unknown",
        }
        
        try:
            if self._sync_pool:
                # Try to get connection pool statistics
                # redis-py ConnectionPool has limited introspection, but we can try
                try:
                    # Get created connections if available (private attribute)
                    created = getattr(self._sync_pool, '_created_connections', None)
                    if created is not None:
                        health["created_connections"] = created
                        health["pool_utilization_percent"] = (
                            (created / self.max_connections) * 100 if self.max_connections > 0 else 0
                        )
                        
                        # Determine health status based on utilization
                        utilization = health["pool_utilization_percent"]
                        if utilization < 70:
                            health["health_status"] = "healthy"
                        elif utilization < 90:
                            health["health_status"] = "warning"
                        else:
                            health["health_status"] = "critical"
                    else:
                        # Can't get detailed stats, assume healthy but note as limited
                        health["health_status"] = "healthy"
                        health["note"] = "Detailed pool stats not available"
                    
                    # Test connection health by trying to ping
                    try:
                        client = self.get_sync_client()
                        client.ping()
                        health["connection_test"] = "ok"
                    except Exception as ping_err:
                        health["connection_test"] = "failed"
                        health["connection_error"] = str(ping_err)
                        health["health_status"] = "warning"
                        
                except Exception as e:
                    logger.debug(f"Could not get detailed pool stats: {e}")
                    health["health_status"] = "unknown"
                    health["error"] = str(e)
            else:
                health["health_status"] = "not_initialized"
            
            # Add usage stats and rate limiting info for context
            try:
                health["usage_stats"] = self.get_usage_stats()
                can_make, error_msg = self.check_rate_limit()
                health["rate_limit_ok"] = can_make
                health["rate_limit_message"] = error_msg
                
                # If rate limit is reached, mark health as warning
                if not can_make and health["health_status"] == "healthy":
                    health["health_status"] = "warning"
            except Exception as e:
                logger.debug(f"Could not get usage stats: {e}")
            
        except Exception as e:
            logger.error(f"Error getting pool health: {e}")
            health["health_status"] = "error"
            health["error"] = str(e)
        
        return health
    
    def close(self):
        """Close all connections"""
        if self._sync_pool:
            self._sync_pool.disconnect()
        # Async client will be closed by async context


# Global Redis pool instance
_redis_pool: Optional[RedisClientPool] = None


def get_redis_pool() -> Optional[RedisClientPool]:
    """
    Get or create global Redis client pool.
    
    Returns None if Redis URL is not configured.
    """
    global _redis_pool
    
    if _redis_pool is None:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return None
        
        use_ssl = "upstash.io" in redis_url or redis_url.startswith("rediss://")
        # Reduced max_connections to 5 for Upstash compatibility
        # Upstash free tier has connection limits, and we want to avoid "Too many connections" errors
        max_conns = int(os.getenv("REDIS_MAX_CONNECTIONS", "5"))
        _redis_pool = RedisClientPool(redis_url, max_connections=max_conns, use_ssl=use_ssl)
    
    return _redis_pool


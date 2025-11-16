"""
Async Rate Limiting Queue Manager
Implements async request queuing for rate limiting with daily limits
"""
import asyncio
import time
import random
from collections import deque
from typing import Callable, Any, Optional, Coroutine
from src.utils.logger import get_logger
from src.rate_limit.daily_limit_manager import get_daily_limit_manager

logger = get_logger(__name__)


class AsyncRequestQueue:
    """Manages async API request rate limiting and queuing"""
    
    def __init__(self, max_rate=2, period=60, safety_margin=0.9, max_daily_requests: Optional[int] = None):
        """
        Args:
            max_rate: Maximum number of requests per period (default 2 for Gemini free tier)
            period: Time period in seconds (default 60 seconds = 1 minute)
            safety_margin: Safety margin multiplier (0.9 = use 90% of max_rate to avoid hitting limits)
            max_daily_requests: Maximum requests per day (default 50 for Gemini free tier)
        """
        # Store original max_rate for reference
        self.original_max_rate = max_rate
        # Apply safety margin to be more conservative
        self.max_rate = int(max_rate * safety_margin)
        self.period = period
        self.request_times = deque()
        self.cache = {}
        self.lock = asyncio.Lock()
        
        # Initialize daily limit manager
        if max_daily_requests is None:
            max_daily_requests = 50  # Gemini free tier default
        self.daily_limit_manager = get_daily_limit_manager(max_daily_requests=max_daily_requests)
        
        logger.debug(
            f"AsyncRequestQueue initialized: max_rate={self.max_rate}/min "
            f"(configured: {max_rate}/min, safety margin: {safety_margin}), "
            f"max_daily={max_daily_requests}/day"
        )
    
    async def _clean_old_requests(self):
        """Remove requests older than the period"""
        current_time = time.time()
        while self.request_times and self.request_times[0] < current_time - self.period:
            self.request_times.popleft()
    
    async def _wait_if_needed(self):
        """Wait if we've hit the rate limit (async)"""
        current_time = time.time()
        
        async with self.lock:
            await self._clean_old_requests()
            
            # Check if we're approaching the rate limit (use 80% threshold for early warning)
            threshold = int(self.max_rate * 0.8)
            if len(self.request_times) >= threshold:
                if len(self.request_times) >= self.max_rate:
                    # Calculate wait time until oldest request expires
                    oldest_request = self.request_times[0]
                    wait_time = (oldest_request + self.period) - current_time + 0.5  # Increased buffer
                    if wait_time > 0:
                        logger.warning(f"⏳ Rate limit reached: Waiting {wait_time:.2f} seconds...")
                        await asyncio.sleep(wait_time)
                        await self._clean_old_requests()
                else:
                    # Approaching limit - add small jitter to spread requests
                    jitter = random.uniform(0, 0.5)
                    if jitter > 0.1:  # Only sleep if jitter is meaningful
                        await asyncio.sleep(jitter)
            
            # Record this request
            self.request_times.append(time.time())
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute an async function with rate limiting (both per-minute and daily limits)
        Also implements basic caching to reduce API calls
        
        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
        
        Returns:
            Function result
        
        Raises:
            ValueError: If daily limit is reached
        
        Note: Rate limit errors (429) should be handled by the provider's retry logic.
        This method focuses on preventing rate limits through request throttling.
        """
        # Generate cache key
        cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.debug("✅ Using cached result")
            return self.cache[cache_key]
        
        # Check daily limit first
        can_make_request, error_msg = self.daily_limit_manager.can_make_request()
        if not can_make_request:
            # Log rate limit error clearly for Celery worker visibility
            logger.error(
                f"❌ RATE LIMIT ERROR: Daily request limit reached. "
                f"{error_msg or 'Daily request limit reached'}"
            )
            # Also print to stderr for Railway visibility
            import sys
            print(
                f"[RATE LIMIT ERROR] Daily request limit reached. "
                f"{error_msg or 'Daily request limit reached'}. "
                f"Please try again tomorrow or upgrade your API plan.",
                file=sys.stderr,
                flush=True
            )
            raise ValueError(error_msg or "Daily request limit reached")
        
        # Apply per-minute rate limiting
        await self._wait_if_needed()
        
        # Record the request for daily tracking
        daily_count = self.daily_limit_manager.record_request()
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            # Cache result (limit cache size to prevent memory issues)
            if len(self.cache) > 100:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[cache_key] = result
            return result
        except Exception as e:
            # Log error but don't suppress it - let the provider handle retries
            error_str = str(e).lower()
            if "429" in error_str or "resource exhausted" in error_str or "rate limit" in error_str:
                logger.error(
                    f"❌ RATE LIMIT ERROR: API rate limit exceeded (429). "
                    f"Error: {str(e)}"
                )
                # Also print to stderr for Railway visibility
                import sys
                print(
                    f"[RATE LIMIT ERROR] API rate limit exceeded (429). "
                    f"Please wait and try again later. Error: {str(e)}",
                    file=sys.stderr,
                    flush=True
                )
                # Don't remove from cache on rate limit errors - we might want to retry
            else:
                logger.error(f"Error executing async function: {e}")
            raise
    
    async def get_stats(self):
        """Get current rate limiting statistics (per-minute and daily)"""
        async with self.lock:
            await self._clean_old_requests()
            daily_stats = self.daily_limit_manager.get_daily_stats()
            
            return {
                "per_minute": {
                    "requests_in_window": len(self.request_times),
                    "max_rate": self.max_rate,
                    "original_max_rate": self.original_max_rate,
                    "utilization_percent": round((len(self.request_times) / self.max_rate * 100) if self.max_rate > 0 else 0, 1)
                },
                "daily": daily_stats,
                "cache_size": len(self.cache)
            }


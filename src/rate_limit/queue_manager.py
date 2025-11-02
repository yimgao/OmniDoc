"""
Rate Limiting Queue Manager
Implements request queuing to stay within Google Gemini free tier limits (60 req/min)
"""
import time
from collections import deque
from functools import wraps
from threading import Lock


class RequestQueue:
    """Manages API request rate limiting and queuing"""
    
    def __init__(self, max_rate=60, period=60):
        """
        Args:
            max_rate: Maximum number of requests per period
            period: Time period in seconds (default 60 seconds = 1 minute)
        """
        self.max_rate = max_rate
        self.period = period
        self.request_times = deque()
        self.cache = {}
        self.lock = Lock()
    
    def _clean_old_requests(self):
        """Remove requests older than the period"""
        current_time = time.time()
        while self.request_times and self.request_times[0] < current_time - self.period:
            self.request_times.popleft()
    
    def _wait_if_needed(self):
        """Wait if we've hit the rate limit"""
        current_time = time.time()
        
        with self.lock:
            self._clean_old_requests()
            
            if len(self.request_times) >= self.max_rate:
                # Calculate wait time until oldest request expires
                oldest_request = self.request_times[0]
                wait_time = (oldest_request + self.period) - current_time + 0.1  # Small buffer
                if wait_time > 0:
                    print(f"⏳ Rate limit: Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    self._clean_old_requests()
            
            # Record this request
            self.request_times.append(time.time())
    
    def execute(self, func, *args, **kwargs):
        """
        Execute a function with rate limiting
        Also implements basic caching to reduce API calls
        """
        # Generate cache key
        cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
        
        # Check cache first
        if cache_key in self.cache:
            print("✅ Using cached result")
            return self.cache[cache_key]
        
        # Apply rate limiting
        self._wait_if_needed()
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            # Cache result (limit cache size to prevent memory issues)
            if len(self.cache) > 100:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[cache_key] = result
            return result
        except Exception as e:
            print(f"❌ Error executing function: {e}")
            raise
    
    def get_stats(self):
        """Get current rate limiting statistics"""
        with self.lock:
            self._clean_old_requests()
            return {
                "requests_in_window": len(self.request_times),
                "max_rate": self.max_rate,
                "cache_size": len(self.cache)
            }


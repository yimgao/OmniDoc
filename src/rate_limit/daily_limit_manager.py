"""
Daily Rate Limit Manager
Tracks daily API request counts to stay within Gemini free tier daily limits (50 requests/day)
"""
import time
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DailyLimitManager:
    """Manages daily API request limits"""
    
    def __init__(self, max_daily_requests: int = 50, safety_margin: float = 0.9):
        """
        Args:
            max_daily_requests: Maximum number of requests per day (default 50 for Gemini free tier)
            safety_margin: Safety margin multiplier (0.9 = use 90% of max to avoid hitting limits)
        """
        self.original_max_daily = max_daily_requests
        self.max_daily_requests = int(max_daily_requests * safety_margin)
        self.safety_margin = safety_margin
        
        # Track requests by date (YYYY-MM-DD)
        self.daily_counts: Dict[str, int] = {}
        self.lock = Lock()
        
        # Clean up old entries periodically
        self._cleanup_old_entries()
        
        logger.info(
            f"DailyLimitManager initialized: max_daily={self.max_daily_requests}/day "
            f"(configured: {max_daily_requests}/day, safety margin: {safety_margin})"
        )
    
    def _get_today_key(self) -> str:
        """Get today's date key (YYYY-MM-DD)"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _cleanup_old_entries(self, lock_held: bool = False):
        """
        Remove entries older than 2 days
        
        Args:
            lock_held: If True, assumes lock is already held and won't acquire it again
        """
        today = datetime.now()
        cutoff = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        
        if lock_held:
            # Lock already held, just do the cleanup
            keys_to_remove = [key for key in self.daily_counts.keys() if key < cutoff]
            for key in keys_to_remove:
                del self.daily_counts[key]
        else:
            # Need to acquire lock
            with self.lock:
                keys_to_remove = [key for key in self.daily_counts.keys() if key < cutoff]
                for key in keys_to_remove:
                    del self.daily_counts[key]
    
    def can_make_request(self) -> tuple[bool, Optional[str]]:
        """
        Check if we can make a request today
        
        Returns:
            (can_make_request, error_message)
        """
        today_key = self._get_today_key()
        
        # Use blocking acquire - this will be run in executor, so blocking is OK
        # The timeout is handled at the async level in AsyncRequestQueue
        self.lock.acquire()
        
        try:
            self._cleanup_old_entries(lock_held=True)  # Lock already held
            
            today_count = self.daily_counts.get(today_key, 0)
            
            if today_count >= self.max_daily_requests:
                remaining = self.max_daily_requests - today_count
                error_msg = (
                    f"Daily request limit reached: {today_count}/{self.max_daily_requests} requests today. "
                    f"Please try again tomorrow or upgrade your API plan."
                )
                logger.error(
                    f"❌ RATE LIMIT ERROR: Daily request limit reached. "
                    f"{today_count}/{self.max_daily_requests} requests today. "
                    f"Please try again tomorrow or upgrade your API plan."
                )
                # Also print to stderr for Railway visibility
                import sys
                print(
                    f"[RATE LIMIT ERROR] Daily request limit reached: "
                    f"{today_count}/{self.max_daily_requests} requests today. "
                    f"Please try again tomorrow or upgrade your API plan.",
                    file=sys.stderr,
                    flush=True
                )
                logger.debug("DailyLimitManager.can_make_request: EXIT - limit reached")
                return False, error_msg
            
            # Check if approaching limit (80% threshold)
            threshold = int(self.max_daily_requests * 0.8)
            if today_count >= threshold:
                remaining = self.max_daily_requests - today_count
                logger.warning(
                    f"⚠️  Approaching daily limit: {today_count}/{self.max_daily_requests} "
                    f"({remaining} remaining today)"
                )
            
            return True, None
        finally:
            self.lock.release()
    
    def record_request(self) -> int:
        """
        Record a request and return current daily count
        
        Returns:
            Current daily request count
        """
        today_key = self._get_today_key()
        
        with self.lock:
            self._cleanup_old_entries(lock_held=True)  # Lock already held
            
            if today_key not in self.daily_counts:
                self.daily_counts[today_key] = 0
            
            self.daily_counts[today_key] += 1
            current_count = self.daily_counts[today_key]
            
            logger.debug(f"📊 Daily request count: {current_count}/{self.max_daily_requests}")
            
            return current_count
    
    def get_daily_stats(self) -> Dict[str, any]:
        """Get current daily statistics"""
        today_key = self._get_today_key()
        
        with self.lock:
            self._cleanup_old_entries(lock_held=True)  # Lock already held
            
            today_count = self.daily_counts.get(today_key, 0)
            remaining = self.max_daily_requests - today_count
            
            return {
                "date": today_key,
                "requests_today": today_count,
                "max_daily_requests": self.max_daily_requests,
                "original_max_daily": self.original_max_daily,
                "remaining_today": max(0, remaining),
                "utilization_percent": round((today_count / self.max_daily_requests * 100) if self.max_daily_requests > 0 else 0, 1),
                "can_make_request": today_count < self.max_daily_requests
            }
    
    def reset_daily_count(self, date_key: Optional[str] = None):
        """
        Reset daily count for a specific date (or today if None)
        
        Args:
            date_key: Date key (YYYY-MM-DD) or None for today
        """
        if date_key is None:
            date_key = self._get_today_key()
        
        with self.lock:
            if date_key in self.daily_counts:
                del self.daily_counts[date_key]
                logger.info(f"🔄 Reset daily count for {date_key}")


# Global daily limit manager instance
_daily_limit_manager: Optional[DailyLimitManager] = None


def get_daily_limit_manager(max_daily_requests: int = 50) -> DailyLimitManager:
    """Get or create the global daily limit manager"""
    global _daily_limit_manager
    
    if _daily_limit_manager is None:
        _daily_limit_manager = DailyLimitManager(max_daily_requests=max_daily_requests)
    
    return _daily_limit_manager


def reset_daily_limit_manager():
    """Reset the global daily limit manager (for testing)"""
    global _daily_limit_manager
    _daily_limit_manager = None


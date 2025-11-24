"""
Error Handler Utilities
Provides better error handling, retry logic, and graceful degradation
Supports both sync and async functions
"""
from typing import Callable, Any, Optional, TypeVar, List, Coroutine
import time
import asyncio
from functools import wraps
import logging
import inspect

T = TypeVar('T')

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying function calls with exponential backoff
    Supports both sync and async functions
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry on
    
    Example:
        @retry_with_backoff(max_retries=3)
        def api_call():
            # Your code here
            pass
        
        @retry_with_backoff(max_retries=3)
        async def async_api_call():
            # Your async code here
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Check if function is async
        if inspect.iscoroutinefunction(func):
            # Async version
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                last_exception = None
                delay = initial_delay
                
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                                f"Retrying in {delay:.1f}s..."
                            )
                            await asyncio.sleep(delay)
                            delay *= backoff_factor
                        else:
                            logger.error(
                                f"{func.__name__} failed after {max_retries} attempts: {e}"
                            )
                
                if last_exception:
                    raise last_exception
                raise Exception(f"{func.__name__} failed after {max_retries} attempts")
            
            return async_wrapper
        else:
            # Sync version
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                last_exception = None
                delay = initial_delay
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                                f"Retrying in {delay:.1f}s..."
                            )
                            time.sleep(delay)
                            delay *= backoff_factor
                        else:
                            logger.error(
                                f"{func.__name__} failed after {max_retries} attempts: {e}"
                            )
                
                if last_exception:
                    raise last_exception
                raise Exception(f"{func.__name__} failed after {max_retries} attempts")
            
            return sync_wrapper
    
    return decorator


def graceful_degradation(
    fallback_value: Any = None,
    fallback_func: Optional[Callable] = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True
):
    """
    Decorator for graceful degradation on errors
    
    Args:
        fallback_value: Value to return if function fails
        fallback_func: Function to call if primary function fails
        exceptions: Tuple of exceptions to catch
        log_errors: Whether to log errors
    
    Example:
        @graceful_degradation(fallback_value="")
        def get_data():
            # Your code here
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    logger.warning(f"{func.__name__} failed: {e}. Using fallback.")
                
                if fallback_func:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception:
                        pass
                
                return fallback_value
        
        return wrapper
    return decorator


class ErrorHandler:
    """
    Centralized error handling utility
    
    Provides:
    - Retry logic with backoff
    - Graceful degradation
    - Error categorization
    - Recovery strategies
    """
    
    @staticmethod
    def is_retryable_error(error: Exception) -> bool:
        """Check if an error is retryable"""
        retryable_types = (
            ConnectionError,
            TimeoutError,
            OSError,
        )
        
        error_str = str(error).lower()
        retryable_strings = (
            "rate limit",
            "too many requests",
            "timeout",
            "connection",
            "network",
            "temporary"
        )
        
        return (
            isinstance(error, retryable_types) or
            any(retry_str in error_str for retry_str in retryable_strings)
        )
    
    @staticmethod
    def get_error_category(error: Exception) -> str:
        """Categorize error type"""
        if isinstance(error, ConnectionError):
            return "network"
        elif isinstance(error, TimeoutError):
            return "timeout"
        elif isinstance(error, ValueError):
            return "validation"
        elif isinstance(error, KeyError):
            return "missing_data"
        elif "rate limit" in str(error).lower():
            return "rate_limit"
        else:
            return "unknown"
    
    @staticmethod
    def get_recovery_strategy(error: Exception) -> Optional[str]:
        """Get suggested recovery strategy for error"""
        category = ErrorHandler.get_error_category(error)
        
        strategies = {
            "network": "Retry with exponential backoff",
            "timeout": "Increase timeout or retry",
            "rate_limit": "Wait and retry with longer delay",
            "validation": "Fix input data",
            "missing_data": "Provide missing required data",
            "unknown": "Check error message and context"
        }
        
        return strategies.get(category, "Unknown error type")


def safe_execute(
    func: Callable[..., T],
    *args,
    default_value: Any = None,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Optional[T]:
    """
    Safely execute a function and return default value on error
    
    Args:
        func: Function to execute
        *args: Positional arguments
        default_value: Value to return on error
        exceptions: Exceptions to catch
        **kwargs: Keyword arguments
    
    Returns:
        Function result or default_value on error
    """
    try:
        return func(*args, **kwargs)
    except exceptions as e:
        logger.warning(f"Safe execution failed for {func.__name__}: {e}")
        return default_value


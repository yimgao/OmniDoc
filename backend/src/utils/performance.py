"""
Performance Monitoring Utilities
Provides decorators and context managers for performance tracking
"""
import time
import functools
from typing import Callable, Any, Optional
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


def track_performance(
    min_time_ms: float = 0.0,
    log_level: str = "INFO",
    include_args: bool = False
) -> Callable:
    """
    Decorator to track and log function performance
    
    Args:
        min_time_ms: Only log if execution time exceeds this (milliseconds)
        log_level: Log level to use ('DEBUG', 'INFO', 'WARNING')
        include_args: Whether to include function arguments in log
    
    Usage:
        @track_performance(min_time_ms=100, log_level='INFO')
        def my_slow_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            settings = get_settings()
            
            # Skip if performance logging is disabled
            if not settings.enable_performance_logging:
                return func(*args, **kwargs)
            
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                execution_time_ms = (time.perf_counter() - start_time) * 1000
                
                # Only log if exceeds threshold
                if execution_time_ms >= min_time_ms:
                    log_msg = f"{func.__name__} executed in {execution_time_ms:.2f}ms"
                    
                    if include_args and settings.enable_profiling:
                        args_str = str(args)[:100] if args else "()"
                        kwargs_str = str(kwargs)[:100] if kwargs else "{}"
                        log_msg += f" | args={args_str}, kwargs={kwargs_str}"
                    
                    logger.log(
                        getattr(logger, log_level.lower(), logger.info),
                        log_msg,
                        extra={
                            'extra_fields': {
                                'execution_time_ms': execution_time_ms,
                                'execution_time_seconds': execution_time_ms / 1000,
                                'function': func.__name__,
                                'module': func.__module__
                            }
                        }
                    )
                
                return result
                
            except Exception as e:
                execution_time_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"{func.__name__} failed after {execution_time_ms:.2f}ms: {str(e)}",
                    exc_info=True,
                    extra={
                        'extra_fields': {
                            'execution_time_ms': execution_time_ms,
                            'function': func.__name__
                        }
                    }
                )
                raise
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Context manager for performance monitoring"""
    
    def __init__(self, operation_name: str, logger_instance: Optional[Any] = None):
        """
        Initialize performance monitor
        
        Args:
            operation_name: Name of the operation being monitored
            logger_instance: Optional logger (defaults to module logger)
        """
        self.operation_name = operation_name
        self.logger = logger_instance or logger
        self.start_time = None
        self.settings = get_settings()
    
    def __enter__(self):
        if self.settings.enable_performance_logging:
            self.start_time = time.perf_counter()
            self.logger.debug(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.settings.enable_performance_logging and self.start_time:
            execution_time_ms = (time.perf_counter() - self.start_time) * 1000
            
            if exc_type:
                self.logger.error(
                    f"Failed: {self.operation_name} after {execution_time_ms:.2f}ms",
                    exc_info=(exc_type, exc_val, exc_tb),
                    extra={
                        'extra_fields': {
                            'execution_time_ms': execution_time_ms,
                            'operation': self.operation_name
                        }
                    }
                )
            else:
                self.logger.info(
                    f"Completed: {self.operation_name} in {execution_time_ms:.2f}ms",
                    extra={
                        'extra_fields': {
                            'execution_time_ms': execution_time_ms,
                            'execution_time_seconds': execution_time_ms / 1000,
                            'operation': self.operation_name
                        }
                    }
                )
        
        return False  # Don't suppress exceptions


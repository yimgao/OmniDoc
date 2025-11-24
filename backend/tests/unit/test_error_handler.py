"""
Unit Tests: ErrorHandler
Fast, isolated tests for error handling utilities
"""
import pytest
from src.utils.error_handler import (
    ErrorHandler,
    retry_with_backoff,
    graceful_degradation,
    safe_execute
)


@pytest.mark.unit
class TestErrorHandler:
    """Test ErrorHandler class"""
    
    def test_is_retryable_error(self):
        """Test retryable error detection"""
        assert ErrorHandler.is_retryable_error(ConnectionError("Connection failed"))
        assert ErrorHandler.is_retryable_error(TimeoutError("Timeout"))
        assert ErrorHandler.is_retryable_error(Exception("Rate limit exceeded"))
        assert not ErrorHandler.is_retryable_error(ValueError("Invalid input"))
    
    def test_get_error_category(self):
        """Test error categorization"""
        assert ErrorHandler.get_error_category(ConnectionError()) == "network"
        assert ErrorHandler.get_error_category(TimeoutError()) == "timeout"
        assert ErrorHandler.get_error_category(ValueError()) == "validation"
        assert ErrorHandler.get_error_category(KeyError()) == "missing_data"
    
    def test_get_recovery_strategy(self):
        """Test recovery strategy suggestions"""
        strategy = ErrorHandler.get_recovery_strategy(ConnectionError())
        assert "retry" in strategy.lower() or "backoff" in strategy.lower()
    
    def test_retry_decorator_success(self):
        """Test retry decorator on successful call"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_decorator_failure_then_success(self):
        """Test retry decorator with eventual success"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_decorator_all_fail(self):
        """Test retry decorator when all attempts fail"""
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def test_func():
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError):
            test_func()
    
    def test_graceful_degradation_with_value(self):
        """Test graceful degradation with fallback value"""
        @graceful_degradation(fallback_value="fallback")
        def test_func():
            raise ValueError("Error")
        
        result = test_func()
        assert result == "fallback"
    
    def test_graceful_degradation_with_func(self):
        """Test graceful degradation with fallback function"""
        def fallback():
            return "fallback_result"
        
        @graceful_degradation(fallback_func=fallback)
        def test_func():
            raise ValueError("Error")
        
        result = test_func()
        assert result == "fallback_result"
    
    def test_safe_execute_success(self):
        """Test safe_execute on successful call"""
        def test_func(x, y):
            return x + y
        
        result = safe_execute(test_func, 2, 3)
        assert result == 5
    
    def test_safe_execute_failure(self):
        """Test safe_execute on failed call"""
        def test_func():
            raise ValueError("Error")
        
        result = safe_execute(test_func, default_value="default")
        assert result == "default"


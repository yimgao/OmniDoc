"""
Tests for monitoring and metrics functionality
"""
import pytest

from src.web.monitoring import (
    increment_counter,
    record_timing,
    get_metric,
    get_timing_stats,
    TimingContext,
)


def test_increment_counter():
    """Test counter increment"""
    increment_counter("test.counter")
    assert get_metric("test.counter") == 1
    
    increment_counter("test.counter", 5)
    assert get_metric("test.counter") == 6


def test_record_timing():
    """Test timing recording"""
    record_timing("test.timing", 0.123)
    stats = get_timing_stats("test.timing")
    assert stats is not None
    assert stats["min"] == 0.123
    assert stats["max"] == 0.123
    assert stats["avg"] == 0.123
    assert stats["count"] == 1


def test_timing_context():
    """Test timing context manager"""
    import time
    
    with TimingContext("test.context"):
        time.sleep(0.01)  # Small delay
    
    stats = get_timing_stats("test.context")
    assert stats is not None
    assert stats["count"] == 1
    assert stats["min"] >= 0.01


def test_get_all_metrics():
    """Test getting all metrics"""
    from src.web.monitoring import get_all_metrics
    
    increment_counter("test.metric1")
    increment_counter("test.metric2", 2)
    
    all_metrics = get_all_metrics()
    assert "test.metric1" in all_metrics
    assert "test.metric2" in all_metrics
    assert all_metrics["test.metric1"] >= 1
    assert all_metrics["test.metric2"] >= 2


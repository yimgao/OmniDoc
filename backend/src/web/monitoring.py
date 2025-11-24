"""
Monitoring and metrics utilities for the OmniDoc API.

This module provides utilities for tracking application metrics,
performance monitoring, and health checks.

Metrics tracked:
- Request counts by endpoint
- Response times
- Error rates
- Rate limit violations
- WebSocket connection counts
- Task queue metrics

Note:
    In production, consider integrating with:
    - Prometheus for metrics collection
    - Grafana for visualization
    - Sentry for error tracking
    - DataDog/New Relic for APM
"""
from __future__ import annotations

import time
from typing import Dict, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Simple in-memory metrics (for development)
# In production, use a proper metrics backend
_metrics: Dict[str, int] = {}
_timings: Dict[str, list] = {}


def increment_counter(metric_name: str, value: int = 1) -> None:
    """
    Increment a counter metric.
    
    Args:
        metric_name: Name of the metric (e.g., "api.requests.total")
        value: Amount to increment (default: 1)
    
    Example:
        >>> increment_counter("api.requests.total")
        >>> increment_counter("api.errors.rate_limit", 5)
    """
    _metrics[metric_name] = _metrics.get(metric_name, 0) + value
    logger.debug(f"Metric {metric_name} incremented by {value} (total: {_metrics[metric_name]})")


def record_timing(metric_name: str, duration: float) -> None:
    """
    Record a timing metric.
    
    Args:
        metric_name: Name of the metric (e.g., "api.response_time")
        duration: Duration in seconds
    
    Example:
        >>> record_timing("api.response_time", 0.123)
    """
    if metric_name not in _timings:
        _timings[metric_name] = []
    _timings[metric_name].append(duration)
    
    # Keep only last 1000 timings to prevent memory issues
    if len(_timings[metric_name]) > 1000:
        _timings[metric_name] = _timings[metric_name][-1000:]
    
    logger.debug(f"Timing {metric_name}: {duration:.3f}s")


def get_metric(metric_name: str) -> int:
    """
    Get current value of a counter metric.
    
    Args:
        metric_name: Name of the metric
    
    Returns:
        Current counter value (0 if not set)
    """
    return _metrics.get(metric_name, 0)


def get_timing_stats(metric_name: str) -> Optional[Dict[str, float]]:
    """
    Get statistics for a timing metric.
    
    Args:
        metric_name: Name of the metric
    
    Returns:
        Dictionary with min, max, avg, count, or None if no data
    """
    if metric_name not in _timings or not _timings[metric_name]:
        return None
    
    timings = _timings[metric_name]
    return {
        "min": min(timings),
        "max": max(timings),
        "avg": sum(timings) / len(timings),
        "count": len(timings),
    }


def get_all_metrics() -> Dict[str, int]:
    """
    Get all counter metrics.
    
    Returns:
        Dictionary of all metric names and values
    """
    return _metrics.copy()


class TimingContext:
    """
    Context manager for timing code execution.
    
    Usage:
        with TimingContext("api.endpoint.duration"):
            # Code to time
            pass
    """
    
    def __init__(self, metric_name: str):
        """
        Initialize timing context.
        
        Args:
            metric_name: Name of the metric to record
        """
        self.metric_name = metric_name
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metric"""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            record_timing(self.metric_name, duration)


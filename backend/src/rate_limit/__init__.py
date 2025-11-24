"""
Rate limiting utilities for API and LLM provider requests.

This module provides rate limiting functionality to:
- Prevent API abuse
- Manage LLM provider rate limits
- Queue requests when limits are exceeded
- Support both sync and async operations

Components:
- RequestQueue: Synchronous rate limiting queue
- AsyncRequestQueue: Asynchronous rate limiting queue
"""

"""
Utility functions for web application.

This module provides helper functions used across the web API,
including JSON parsing utilities and common data transformations.
"""
from __future__ import annotations

import json
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_json_field(value: Any, default: Any = None) -> Any:
    """
    Parse a JSON field that may be a string, list, dict, or already parsed.
    
    This function handles the common case where database fields may store
    JSON as strings (from older migrations) or as already-parsed objects.
    
    Args:
        value: The value to parse (can be str, list, dict, or None)
        default: Default value to return if parsing fails or value is None
        
    Returns:
        Parsed value or default. If value is a string, attempts JSON parsing.
        If parsing fails, returns default. If value is already a dict/list,
        returns it as-is.
    
    Example:
        >>> parse_json_field('["a", "b"]')  # Returns: ["a", "b"]
        >>> parse_json_field(["a", "b"])   # Returns: ["a", "b"]
        >>> parse_json_field(None)          # Returns: None (or default)
        >>> parse_json_field("invalid")     # Returns: None (or default)
    """
    if value is None:
        return default
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON field: %s", value[:100] if len(str(value)) > 100 else value)
            return default
    
    return value


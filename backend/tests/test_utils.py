"""
Tests for utility functions
"""
import pytest

from src.web.utils import parse_json_field


def test_parse_json_field_string():
    """Test parsing JSON string"""
    result = parse_json_field('["a", "b"]')
    assert result == ["a", "b"]


def test_parse_json_field_already_parsed():
    """Test parsing already parsed JSON"""
    result = parse_json_field(["a", "b"])
    assert result == ["a", "b"]


def test_parse_json_field_none():
    """Test parsing None value"""
    result = parse_json_field(None)
    assert result is None


def test_parse_json_field_none_with_default():
    """Test parsing None with default value"""
    result = parse_json_field(None, default=[])
    assert result == []


def test_parse_json_field_invalid_json():
    """Test parsing invalid JSON string"""
    result = parse_json_field("invalid json")
    assert result is None


def test_parse_json_field_invalid_json_with_default():
    """Test parsing invalid JSON with default value"""
    result = parse_json_field("invalid json", default=[])
    assert result == []


def test_parse_json_field_dict():
    """Test parsing dictionary"""
    result = parse_json_field({"key": "value"})
    assert result == {"key": "value"}


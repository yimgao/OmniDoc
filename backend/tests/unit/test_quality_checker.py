"""
Unit Tests: QualityChecker
Fast, isolated tests for quality checking
"""
import pytest


@pytest.mark.unit
class TestQualityChecker:
    """Test QualityChecker class"""
    
    def test_check_word_count(self, quality_checker):
        """Test word count checking"""
        content = "This is a test document with enough words to pass the minimum threshold requirement."
        result = quality_checker.check_word_count(content)
        
        assert "word_count" in result
        assert "score" in result
        assert "passed" in result
        assert result["word_count"] > 0
    
    def test_check_word_count_below_threshold(self, quality_checker):
        """Test word count below threshold"""
        content = "Short"
        result = quality_checker.check_word_count(content)
        
        assert result["passed"] is False
        assert result["word_count"] < quality_checker.min_words
    
    def test_check_sections(self, quality_checker):
        """Test section completeness checking"""
        content = """
# Project Overview
Some content

## Core Features
Feature list

## Technical Requirements
Tech specs
"""
        result = quality_checker.check_sections(content)
        
        assert "completeness_score" in result
        assert "found_sections" in result
        assert "missing_sections" in result
    
    def test_check_sections_missing(self, quality_checker):
        """Test section check with missing sections"""
        content = "# Only one section"
        result = quality_checker.check_sections(content)
        
        assert len(result["missing_sections"]) > 0
    
    def test_check_readability(self, quality_checker):
        """Test readability checking"""
        content = """
        This is a simple sentence. It is easy to read.
        The content uses common words and short sentences.
        """
        result = quality_checker.check_readability(content)
        
        assert "readability_score" in result
        assert "level" in result
        assert "passed" in result
    
    def test_check_quality_comprehensive(self, quality_checker):
        """Test comprehensive quality check"""
        content = """
# Project Overview
This is a comprehensive project overview that provides context.

## Core Features
- Feature one
- Feature two
- Feature three

## Technical Requirements
Technical specifications here.

## User Personas
User information.

## Business Objectives
Business goals.

## Constraints
Project constraints.
"""
        result = quality_checker.check_quality(content)
        
        assert "overall_score" in result
        assert "passed" in result
        assert "word_count" in result
        assert "sections" in result
        assert "readability" in result
    
    def test_check_quality_weights(self, quality_checker):
        """Test custom quality weights"""
        content = "Test content with sufficient sections and words."
        custom_weights = {
            "word_count": 0.5,
            "completeness": 0.3,
            "readability": 0.2
        }
        result = quality_checker.check_quality(content, weights=custom_weights)
        
        assert "overall_score" in result
        assert result["weights"] == custom_weights


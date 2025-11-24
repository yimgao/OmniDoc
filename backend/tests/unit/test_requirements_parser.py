"""
Unit Tests: RequirementsParser
Fast, isolated tests for requirements parsing
"""
import pytest
from src.utils.requirements_parser import RequirementsParser
from src.context.shared_context import RequirementsDocument


@pytest.mark.unit
class TestRequirementsParser:
    """Test RequirementsParser class"""
    
    @pytest.fixture
    def parser(self):
        """Fixture for RequirementsParser"""
        return RequirementsParser()
    
    @pytest.fixture
    def sample_markdown(self):
        """Sample requirements markdown"""
        return """
# Project Overview
This is a simple blog platform for users to share their thoughts.

## Core Features
- User authentication
- Post creation and editing
- Comment system
- Tag management

## Technical Requirements
- Backend: Python with FastAPI
- Database: PostgreSQL
- Frontend: React
- Deployment: Docker

## User Personas
- **Blog Author**: Wants to write and publish posts
- **Reader**: Wants to read and comment on posts

## Business Objectives
- Increase user engagement
- Generate ad revenue
- Build community

## Constraints and Assumptions
- Must work on mobile devices
- Assumes users have basic web knowledge
"""
    
    def test_parse_markdown_basic(self, parser, sample_markdown):
        """Test basic markdown parsing"""
        result = parser.parse_markdown(sample_markdown, "Blog platform")
        
        assert isinstance(result, RequirementsDocument)
        assert len(result.core_features) > 0
        assert len(result.technical_requirements) > 0
    
    def test_extract_core_features(self, parser, sample_markdown):
        """Test extraction of core features"""
        result = parser.parse_markdown(sample_markdown, "Blog platform")
        
        assert "user authentication" in " ".join(result.core_features).lower()
        assert len(result.core_features) >= 3
    
    def test_extract_technical_requirements(self, parser, sample_markdown):
        """Test extraction of technical requirements"""
        result = parser.parse_markdown(sample_markdown, "Blog platform")
        
        assert len(result.technical_requirements) > 0
        # Should have extracted backend, database, etc.
        assert any("python" in v.lower() or "fastapi" in v.lower() 
                  for v in result.technical_requirements.values())
    
    def test_extract_user_personas(self, parser, sample_markdown):
        """Test extraction of user personas"""
        result = parser.parse_markdown(sample_markdown, "Blog platform")
        
        assert len(result.user_personas) > 0
        assert all("name" in persona for persona in result.user_personas)
    
    def test_extract_business_objectives(self, parser, sample_markdown):
        """Test extraction of business objectives"""
        result = parser.parse_markdown(sample_markdown, "Blog platform")
        
        assert len(result.business_objectives) > 0
        assert any("engagement" in obj.lower() for obj in result.business_objectives)
    
    def test_extract_constraints(self, parser, sample_markdown):
        """Test extraction of constraints"""
        result = parser.parse_markdown(sample_markdown, "Blog platform")
        
        assert len(result.constraints) > 0 or len(result.assumptions) > 0
    
    def test_empty_markdown(self, parser):
        """Test parsing empty markdown"""
        result = parser.parse_markdown("", "Test idea")
        
        assert isinstance(result, RequirementsDocument)
        assert result.user_idea == "Test idea"


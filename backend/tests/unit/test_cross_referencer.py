"""
Unit Tests: CrossReferencer
Fast, isolated tests for cross-referencing system
"""
import pytest
from src.utils.cross_referencer import CrossReferencer
from src.context.shared_context import AgentType


@pytest.mark.unit
class TestCrossReferencer:
    """Test CrossReferencer class"""
    
    @pytest.fixture
    def cross_referencer(self):
        """Fixture for CrossReferencer"""
        return CrossReferencer()
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing"""
        return {
            AgentType.REQUIREMENTS_ANALYST: "# Requirements\n\nProject requirements here.",
            AgentType.PM_DOCUMENTATION: "# Project Plan\n\nPM documentation here.",
            AgentType.TECHNICAL_DOCUMENTATION: "# Technical Spec\n\nTechnical details here."
        }
    
    @pytest.fixture
    def sample_file_paths(self):
        """Sample file paths for testing"""
        return {
            AgentType.REQUIREMENTS_ANALYST: "docs/requirements.md",
            AgentType.PM_DOCUMENTATION: "docs/pm/project_plan.md",
            AgentType.TECHNICAL_DOCUMENTATION: "docs/technical/technical_spec.md"
        }
    
    def test_add_cross_references(self, cross_referencer, sample_documents, sample_file_paths):
        """Test adding cross-references to a document"""
        content = sample_documents[AgentType.REQUIREMENTS_ANALYST]
        result = cross_referencer.add_cross_references(
            content,
            AgentType.REQUIREMENTS_ANALYST,
            sample_documents,
            sample_file_paths
        )
        
        assert "## See Also" in result
        assert "Project Plan" in result or "PM" in result
    
    def test_generate_document_index(self, cross_referencer, sample_documents, sample_file_paths):
        """Test generating document index"""
        index = cross_referencer.generate_document_index(
            sample_documents,
            sample_file_paths,
            "Test Project"
        )
        
        assert "# Test Project - Documentation Index" in index
        assert "requirements.md" in index
        assert "project_plan.md" in index
        assert "technical_spec.md" in index
    
    def test_create_cross_references(self, cross_referencer, sample_documents, sample_file_paths):
        """Test creating cross-references for all documents"""
        referenced = cross_referencer.create_cross_references(
            sample_documents,
            sample_file_paths
        )
        
        assert len(referenced) == len(sample_documents)
        
        # Check that at least one has "See Also"
        has_references = any("See Also" in content for content in referenced.values())
        assert has_references
    
    def test_empty_documents(self, cross_referencer):
        """Test with empty documents"""
        index = cross_referencer.generate_document_index({}, {}, "Test")
        assert "Documentation Index" in index
    
    def test_see_also_section_format(self, cross_referencer, sample_documents, sample_file_paths):
        """Test that See Also section is properly formatted"""
        content = sample_documents[AgentType.REQUIREMENTS_ANALYST]
        result = cross_referencer.add_cross_references(
            content,
            AgentType.REQUIREMENTS_ANALYST,
            sample_documents,
            sample_file_paths
        )
        
        # Should have markdown links
        assert "](" in result
        # Should have bullet points
        assert "-" in result or "*" in result


"""
Unit Tests: QualityReviewerAgent
Fast, isolated tests for quality reviewer agent
"""
import pytest
from src.agents.quality_reviewer_agent import QualityReviewerAgent


@pytest.mark.unit
class TestQualityReviewerAgent:
    """Test QualityReviewerAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager, quality_checker):
        """Test agent initialization"""
        agent = QualityReviewerAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager,
            quality_checker=quality_checker
        )
        
        assert agent.agent_name == "QualityReviewerAgent"
        assert agent.file_manager is not None
        assert agent.quality_checker is not None
    
    def test_generate_quality_review(self, mock_llm_provider, file_manager, quality_checker):
        """Test generating quality review"""
        agent = QualityReviewerAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager,
            quality_checker=quality_checker
        )
        
        all_docs = {
            "requirements.md": "# Project Overview\n\nThis is a test project.",
            "technical_spec.md": "# Technical Spec\n\nPython backend."
        }
        
        result = agent.generate(all_docs)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_and_save(self, mock_llm_provider, file_manager, quality_checker):
        """Test generating and saving quality review"""
        agent = QualityReviewerAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager,
            quality_checker=quality_checker
        )
        
        all_docs = {
            "requirements.md": "# Test Doc\n\nContent here."
        }
        
        file_path = agent.generate_and_save(all_docs, output_filename="review.md")
        
        assert file_path is not None
        assert file_manager.file_exists("review.md")


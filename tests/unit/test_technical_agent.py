"""
Unit Tests: TechnicalDocumentationAgent
Fast, isolated tests for technical documentation agent
"""
import pytest
from src.agents.technical_documentation_agent import TechnicalDocumentationAgent


@pytest.mark.unit
class TestTechnicalDocumentationAgent:
    """Test TechnicalDocumentationAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager):
        """Test agent initialization"""
        agent = TechnicalDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        assert agent.agent_name == "TechnicalDocumentationAgent"
        assert agent.file_manager is not None
    
    def test_generate_technical_doc(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating technical documentation"""
        agent = TechnicalDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        # Provide required dependencies (user_stories or pm_summary)
        user_stories_summary = "## User Story 1\nAs a user, I want to create blog posts"
        result = agent.generate(sample_requirements_summary, user_stories_summary=user_stories_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_and_save(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating and saving technical documentation"""
        agent = TechnicalDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        # Provide required dependencies (user_stories or pm_summary)
        user_stories_summary = "## User Story 1\nAs a user, I want to create blog posts"
        file_path = agent.generate_and_save(
            sample_requirements_summary, 
            user_stories_summary=user_stories_summary,
            output_filename="technical_spec.md"
        )
        
        assert file_path is not None
        assert file_manager.file_exists("technical_spec.md")


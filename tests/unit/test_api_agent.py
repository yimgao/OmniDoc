"""
Unit Tests: APIDocumentationAgent
Fast, isolated tests for API documentation agent
"""
import pytest
from src.agents.api_documentation_agent import APIDocumentationAgent


@pytest.mark.unit
class TestAPIDocumentationAgent:
    """Test APIDocumentationAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager):
        """Test agent initialization"""
        agent = APIDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        assert agent.agent_name == "APIDocumentationAgent"
        assert agent.file_manager is not None
    
    def test_generate_api_doc(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating API documentation"""
        agent = APIDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        # Provide required technical_summary dependency
        technical_summary = "## System Architecture\nREST API with FastAPI"
        result = agent.generate(sample_requirements_summary, technical_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_api_doc_with_technical(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating API documentation with technical summary"""
        agent = APIDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        technical_summary = "## System Architecture\nREST API with FastAPI"
        result = agent.generate(sample_requirements_summary, technical_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_and_save(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating and saving API documentation"""
        agent = APIDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        # Provide required technical_summary dependency
        technical_summary = "## System Architecture\nREST API with FastAPI"
        file_path = agent.generate_and_save(
            sample_requirements_summary, 
            technical_summary=technical_summary,
            output_filename="api_docs.md"
        )
        
        assert file_path is not None
        assert file_manager.file_exists("api_docs.md")


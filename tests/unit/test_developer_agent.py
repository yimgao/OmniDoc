"""
Unit Tests: DeveloperDocumentationAgent
Fast, isolated tests for developer documentation agent
"""
import pytest
from src.agents.developer_documentation_agent import DeveloperDocumentationAgent


@pytest.mark.unit
class TestDeveloperDocumentationAgent:
    """Test DeveloperDocumentationAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager):
        """Test agent initialization"""
        agent = DeveloperDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        assert agent.agent_name == "DeveloperDocumentationAgent"
        assert agent.file_manager is not None
    
    def test_generate_developer_doc(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating developer documentation"""
        agent = DeveloperDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        result = agent.generate(sample_requirements_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_developer_doc_with_context(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating developer documentation with technical and API summaries"""
        agent = DeveloperDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        technical_summary = "## System Architecture\nREST API with FastAPI"
        api_summary = "## API Endpoints\nGET /api/users"
        result = agent.generate(sample_requirements_summary, technical_summary, api_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_and_save(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating and saving developer documentation"""
        agent = DeveloperDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        file_path = agent.generate_and_save(sample_requirements_summary, output_filename="dev_guide.md")
        
        assert file_path is not None
        assert file_manager.file_exists("dev_guide.md")


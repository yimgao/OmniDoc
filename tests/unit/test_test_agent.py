"""
Unit Tests: TestDocumentationAgent
Fast, isolated tests for test documentation agent
"""
import pytest
from src.agents.test_documentation_agent import TestDocumentationAgent


@pytest.mark.unit
class TestTestDocumentationAgent:
    """Test TestDocumentationAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager):
        """Test agent initialization"""
        agent = TestDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        assert agent.agent_name == "TestDocumentationAgent"
        assert agent.file_manager is not None
    
    def test_generate_test_doc(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating test documentation"""
        agent = TestDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        # Provide required technical_summary dependency
        technical_summary = "## System Architecture\nREST API with FastAPI"
        result = agent.generate(sample_requirements_summary, technical_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_test_doc_with_technical(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating test documentation with technical summary"""
        agent = TestDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        technical_summary = "## System Architecture\nREST API with FastAPI"
        result = agent.generate(sample_requirements_summary, technical_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_and_save(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating and saving test documentation"""
        agent = TestDocumentationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        # Provide required technical_summary dependency
        technical_summary = "## System Architecture\nREST API with FastAPI"
        file_path = agent.generate_and_save(
            sample_requirements_summary, 
            technical_summary=technical_summary,
            output_filename="test_plan.md"
        )
        
        assert file_path is not None
        assert file_manager.file_exists("test_plan.md")


"""
Integration Tests: RequirementsAnalyst Agent
Tests agent with real or mocked LLM provider
"""
import pytest
from src.agents.requirements_analyst import RequirementsAnalyst
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType


@pytest.mark.integration
class TestRequirementsAnalyst:
    """Integration tests for RequirementsAnalyst"""
    
    def test_generate_requirements(self, mock_llm_provider, file_manager):
        """Test generating requirements with mocked LLM"""
        agent = RequirementsAnalyst(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        result = agent.generate("Build a blog platform")
        
        assert result is not None
        assert len(result) > 0
        assert "Test Document" in result or "Section" in result
    
    def test_generate_and_save(self, mock_llm_provider, file_manager):
        """Test generating and saving requirements"""
        agent = RequirementsAnalyst(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        file_path = agent.generate_and_save("Build a blog", "requirements.md")
        
        assert file_path is not None
        assert file_manager.file_exists("requirements.md")
    
    @pytest.mark.requires_api
    @pytest.mark.slow
    def test_generate_with_real_api(self, api_key_available, file_manager):
        """Test with real Gemini API (requires API key)"""
        if not api_key_available["gemini"]:
            pytest.skip("GEMINI_API_KEY not available")
        
        agent = RequirementsAnalyst(file_manager=file_manager)
        
        result = agent.generate("Build a simple todo app")
        
        assert result is not None
        assert len(result) > 100  # Should have substantial content
    
    def test_generate_with_context(self, mock_llm_provider, context_manager, file_manager, test_project_id):
        """Test generating requirements with context sharing"""
        agent = RequirementsAnalyst(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        file_path = agent.generate_and_save(
            "Build a blog",
            "requirements.md",
            project_id=test_project_id,
            context_manager=context_manager
        )
        
        # Check context was saved
        context = context_manager.get_shared_context(test_project_id)
        # Context should have the project created
        assert context.project_id == test_project_id
        
        # Check agent output was saved
        output = context_manager.get_agent_output(test_project_id, AgentType.REQUIREMENTS_ANALYST)
        assert output is not None
        assert output.file_path == file_path


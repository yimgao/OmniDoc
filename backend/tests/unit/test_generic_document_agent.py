"""
Unit Tests: GenericDocumentAgent
Fast, isolated tests for the generic document agent
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.agents.generic_document_agent import GenericDocumentAgent
from src.config.document_catalog import DocumentDefinition


@pytest.mark.unit
class TestGenericDocumentAgent:
    """Test GenericDocumentAgent class"""

    @pytest.fixture
    def sample_definition(self):
        """Create a sample document definition"""
        return DocumentDefinition(
            id="test_doc",
            name="Test Document",
            prompt_key="TEST_PROMPT",
            agent_class="generic",
            dependencies=[],
            category="Test",
            description="A test document",
        )

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider"""
        provider = Mock()
        provider.generate_text = Mock(return_value="# Test Document\n\nThis is test content.")
        provider.async_generate_text = AsyncMock(return_value="# Test Document\n\nThis is test content.")
        return provider

    def test_agent_initialization(self, sample_definition, mock_llm_provider, temp_dir):
        """Test agent initialization"""
        agent = GenericDocumentAgent(
            definition=sample_definition,
            base_output_dir=str(temp_dir),
        )
        agent.llm_provider = mock_llm_provider

        assert agent.definition.id == "test_doc"
        assert agent.definition.name == "Test Document"
        assert agent.output_filename == "test_doc.md"
        assert agent.file_manager is not None

    def test_build_prompt(self, sample_definition, mock_llm_provider, temp_dir):
        """Test prompt building"""
        agent = GenericDocumentAgent(
            definition=sample_definition,
            base_output_dir=str(temp_dir),
        )
        agent.llm_provider = mock_llm_provider

        user_idea = "Create a todo app"
        dependency_documents = {}

        prompt = agent._build_prompt(user_idea, dependency_documents)

        assert "Test Document" in prompt
        assert "Create a todo app" in prompt
        assert "A test document" in prompt

    def test_build_prompt_with_dependencies(self, sample_definition, mock_llm_provider, temp_dir):
        """Test prompt building with dependency documents"""
        agent = GenericDocumentAgent(
            definition=sample_definition,
            base_output_dir=str(temp_dir),
        )
        agent.llm_provider = mock_llm_provider

        user_idea = "Create a todo app"
        dependency_documents = {
            "requirements": {
                "name": "Requirements",
                "content": "The app should have user authentication"
            }
        }

        prompt = agent._build_prompt(user_idea, dependency_documents)

        assert "Requirements" in prompt
        assert "user authentication" in prompt

    def test_generate(self, sample_definition, mock_llm_provider, temp_dir):
        """Test document generation"""
        agent = GenericDocumentAgent(
            definition=sample_definition,
            base_output_dir=str(temp_dir),
        )
        agent.llm_provider = mock_llm_provider

        user_idea = "Create a todo app"
        dependency_documents = {}

        result = agent.generate(user_idea, dependency_documents)

        assert result is not None
        assert len(result) > 0
        assert "# Test Document" in result
        mock_llm_provider.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_generate(self, sample_definition, mock_llm_provider, temp_dir):
        """Test async document generation"""
        agent = GenericDocumentAgent(
            definition=sample_definition,
            base_output_dir=str(temp_dir),
        )
        agent.llm_provider = mock_llm_provider

        user_idea = "Create a todo app"
        dependency_documents = {}

        result = await agent.async_generate(user_idea, dependency_documents)

        assert result is not None
        assert len(result) > 0
        assert "# Test Document" in result
        mock_llm_provider.async_generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_and_save(self, sample_definition, mock_llm_provider, temp_dir):
        """Test generate and save functionality"""
        agent = GenericDocumentAgent(
            definition=sample_definition,
            base_output_dir=str(temp_dir),
        )
        agent.llm_provider = mock_llm_provider

        user_idea = "Create a todo app"
        dependency_documents = {}
        output_rel_path = "test_project/test_doc.md"

        result = await agent.generate_and_save(
            user_idea=user_idea,
            dependency_documents=dependency_documents,
            output_rel_path=output_rel_path,
        )

        assert result["id"] == "test_doc"
        assert result["name"] == "Test Document"
        assert result["file_path"] is not None
        assert Path(result["file_path"]).exists()
        assert "generated_at" in result

        # Verify file content
        file_content = Path(result["file_path"]).read_text()
        assert "# Test Document" in file_content

    def test_prompt_registry_integration(self, sample_definition, mock_llm_provider, temp_dir):
        """Test that specialized prompts are used when available"""
        # Create a definition that should use a specialized prompt
        req_definition = DocumentDefinition(
            id="requirements",
            name="Requirements Document",
            prompt_key="REQUIREMENTS_ANALYST_PROMPT",
            agent_class="generic",
            dependencies=[],
        )

        agent = GenericDocumentAgent(
            definition=req_definition,
            base_output_dir=str(temp_dir),
        )
        agent.llm_provider = mock_llm_provider

        with patch('src.agents.generic_document_agent.get_prompt_for_document') as mock_get_prompt:
            mock_get_prompt.return_value = "Specialized requirements prompt"
            
            prompt = agent._build_prompt("Test idea", {})
            
            assert prompt == "Specialized requirements prompt"
            mock_get_prompt.assert_called_once_with(
                "requirements",
                "Test idea",
                {}
            )


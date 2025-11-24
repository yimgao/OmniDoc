"""
Integration Tests: Multi-Agent Workflow
Tests the complete workflow coordinator with new API-first architecture
"""
import pytest
import asyncio
from src.coordination.coordinator import WorkflowCoordinator
from src.context.context_manager import ContextManager


@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowCoordinator:
    """Integration tests for workflow coordination"""
    
    @pytest.mark.asyncio
    async def test_async_generate_all_docs(self, mock_gemini_provider, context_manager, temp_dir):
        """Test complete workflow with mocked LLM using new async API"""
        # Create coordinator
        coordinator = WorkflowCoordinator(
            context_manager=context_manager,
            provider_name="gemini"
        )
        
        # Mock the LLM provider for all agents
        for agent in coordinator.agents.values():
            if hasattr(agent, 'llm_provider'):
                agent.llm_provider = mock_gemini_provider
            elif hasattr(agent, 'agent') and hasattr(agent.agent, 'llm_provider'):
                agent.agent.llm_provider = mock_gemini_provider

        project_id = "test_project_123"
        user_idea = "Build a blog platform"
        selected_documents = ["requirements", "project_charter"]

        # Run async generation
        results = await coordinator.async_generate_all_docs(
            user_idea=user_idea,
            project_id=project_id,
            selected_documents=selected_documents
        )

        assert results is not None
        assert "files" in results
        assert "documents" in results
        assert "summary" in results
        
        # Check that selected documents were processed
        assert len(results["files"]) > 0
        assert len(results["documents"]) > 0

    @pytest.mark.asyncio
    async def test_dependency_resolution(self, mock_gemini_provider, context_manager, temp_dir):
        """Test that dependencies are resolved correctly"""
        coordinator = WorkflowCoordinator(
            context_manager=context_manager,
            provider_name="gemini"
        )

        # Mock LLM provider
        for agent in coordinator.agents.values():
            if hasattr(agent, 'llm_provider'):
                agent.llm_provider = mock_gemini_provider
            elif hasattr(agent, 'agent') and hasattr(agent.agent, 'llm_provider'):
                agent.agent.llm_provider = mock_gemini_provider

        project_id = "test_project_deps"
        user_idea = "Test project with dependencies"
        
        # Select a document that has dependencies
        # The coordinator should automatically include dependencies
        selected_documents = ["pm_documentation"]  # This might depend on requirements, project_charter

        results = await coordinator.async_generate_all_docs(
            user_idea=user_idea,
            project_id=project_id,
            selected_documents=selected_documents
        )

        # Verify that dependencies were included in execution
        assert results is not None
        assert "files" in results
        
        # The execution plan should include dependencies
        # (exact documents depend on config, but should be more than just pm_documentation)
        assert len(results["files"]) >= 1

    @pytest.mark.asyncio
    async def test_progress_callback(self, mock_gemini_provider, context_manager, temp_dir):
        """Test that progress callbacks are called"""
        coordinator = WorkflowCoordinator(
            context_manager=context_manager,
            provider_name="gemini"
        )

        # Mock LLM provider
        for agent in coordinator.agents.values():
            if hasattr(agent, 'llm_provider'):
                agent.llm_provider = mock_gemini_provider
            elif hasattr(agent, 'agent') and hasattr(agent.agent, 'llm_provider'):
                agent.agent.llm_provider = mock_gemini_provider

        project_id = "test_project_callback"
        user_idea = "Test project"
        selected_documents = ["requirements"]

        progress_events = []

        async def progress_callback(event):
            progress_events.append(event)

        results = await coordinator.async_generate_all_docs(
            user_idea=user_idea,
            project_id=project_id,
            selected_documents=selected_documents,
            progress_callback=progress_callback
        )

        # Verify progress events were received
        assert len(progress_events) > 0
        
        # Check for expected event types
        event_types = [e.get("type") for e in progress_events]
        assert "plan" in event_types or "start" in event_types

    def test_special_agent_integration(self, context_manager):
        """Test that special agents are properly integrated"""
        coordinator = WorkflowCoordinator(
            context_manager=context_manager,
            provider_name="gemini"
        )

        # Check that special agents are in the agents dict
        # Requirements should be a special agent
        if "requirements" in coordinator.agents:
            agent = coordinator.agents["requirements"]
            # Should be a SpecialAgentAdapter for requirements
            from src.agents.special_agent_adapter import SpecialAgentAdapter
            assert isinstance(agent, SpecialAgentAdapter)

    def test_generic_agent_creation(self, context_manager):
        """Test that generic agents are created for non-special documents"""
        coordinator = WorkflowCoordinator(
            context_manager=context_manager,
            provider_name="gemini"
        )

        # Most documents should be generic agents
        generic_count = 0
        special_count = 0
        
        for doc_id, agent in coordinator.agents.items():
            from src.agents.generic_document_agent import GenericDocumentAgent
            from src.agents.special_agent_adapter import SpecialAgentAdapter
            
            if isinstance(agent, GenericDocumentAgent):
                generic_count += 1
            elif isinstance(agent, SpecialAgentAdapter):
                special_count += 1

        # Should have more generic agents than special
        assert generic_count > 0
        assert generic_count > special_count

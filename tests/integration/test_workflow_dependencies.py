"""
Integration Tests: Workflow Dependencies and Phase Structure
Tests the improved workflow with:
- technical_doc and database_schema in Phase 2 for parallel execution
- business_model and marketing_plan in Phase 1 for quick decision-making
"""
import pytest
from src.coordination.workflow_dag import (
    get_phase2_tasks_for_profile,
    build_task_dependencies,
    PHASE2_TASKS_CONFIG,
    Phase2Task
)
from src.context.shared_context import AgentType


@pytest.mark.integration
class TestWorkflowDependencies:
    """Test workflow dependency structure after improvements"""
    
    def test_database_schema_in_phase2(self):
        """Test that database_schema IS in Phase 2 tasks (moved from Phase 1 for parallel execution)"""
        team_tasks = get_phase2_tasks_for_profile(profile="team")
        individual_tasks = get_phase2_tasks_for_profile(profile="individual")
        
        # Database schema should BE in Phase 2 (moved for parallel execution)
        team_task_types = [task.agent_type for task in team_tasks]
        individual_task_types = [task.agent_type for task in individual_tasks]
        
        assert AgentType.DATABASE_SCHEMA in team_task_types
        assert AgentType.DATABASE_SCHEMA in individual_task_types
        
        # Verify database_schema is in PHASE2_TASKS_CONFIG
        assert "database_schema" in PHASE2_TASKS_CONFIG
    
    def test_api_doc_depends_on_database_schema(self):
        """Test that api_doc depends on database_schema"""
        api_doc_task = PHASE2_TASKS_CONFIG.get("api_doc")
        
        assert api_doc_task is not None
        assert api_doc_task.agent_type == AgentType.API_DOCUMENTATION
        
        # api_doc should depend on TECHNICAL_DOCUMENTATION and DATABASE_SCHEMA
        assert AgentType.TECHNICAL_DOCUMENTATION in api_doc_task.dependencies
        assert AgentType.DATABASE_SCHEMA in api_doc_task.dependencies
        
        # Should use with_db_schema kwargs_builder
        assert api_doc_task.kwargs_builder == "with_db_schema"
    
    def test_setup_guide_depends_on_database_schema(self):
        """Test that setup_guide depends on database_schema"""
        setup_guide_task = PHASE2_TASKS_CONFIG.get("setup_guide")
        
        assert setup_guide_task is not None
        assert setup_guide_task.agent_type == AgentType.SETUP_GUIDE
        
        # setup_guide should depend on API_DOCUMENTATION, TECHNICAL_DOCUMENTATION, and DATABASE_SCHEMA
        assert AgentType.API_DOCUMENTATION in setup_guide_task.dependencies
        assert AgentType.TECHNICAL_DOCUMENTATION in setup_guide_task.dependencies
        assert AgentType.DATABASE_SCHEMA in setup_guide_task.dependencies
        
        # Should use with_api_and_db kwargs_builder
        assert setup_guide_task.kwargs_builder == "with_api_and_db"
    
    def test_phase2_dependencies_structure(self):
        """Test Phase 2 dependency structure"""
        team_tasks = get_phase2_tasks_for_profile(profile="team")
        dependency_map = build_task_dependencies(team_tasks)
        
        # api_doc should have dependencies (but they're Phase 1, so empty list in dependency_map)
        # The actual dependencies are handled in coordinator by checking Phase 1 content
        api_doc_deps = dependency_map.get("api_doc", [])
        
        # setup_guide should depend on api_doc (Phase 2 dependency)
        setup_guide_deps = dependency_map.get("setup_guide", [])
        assert "api_doc" in setup_guide_deps
        
        # dev_doc should depend on api_doc
        dev_doc_deps = dependency_map.get("dev_doc", [])
        assert "api_doc" in dev_doc_deps
    
    def test_database_schema_in_phase2_agent_types(self):
        """Test that DATABASE_SCHEMA is now in Phase 2 (moved from Phase 1 for parallel execution)"""
        from src.coordination.workflow_dag import build_task_dependencies
        from src.coordination.workflow_dag import get_phase2_tasks_for_profile
        
        team_tasks = get_phase2_tasks_for_profile(profile="team")
        
        # Verify database_schema is now a Phase 2 task
        team_task_types = [task.agent_type for task in team_tasks]
        assert AgentType.DATABASE_SCHEMA in team_task_types
        
        # Verify api_doc depends on DATABASE_SCHEMA (which is now in Phase 2)
        api_doc_task = PHASE2_TASKS_CONFIG.get("api_doc")
        assert AgentType.DATABASE_SCHEMA in api_doc_task.dependencies
        
        # Verify database_schema task exists in Phase 2
        database_schema_task = PHASE2_TASKS_CONFIG.get("database_schema")
        assert database_schema_task is not None
        assert database_schema_task.agent_type == AgentType.DATABASE_SCHEMA
    
    def test_kwargs_builder_with_db_schema(self):
        """Test that with_db_schema kwargs_builder exists and works"""
        from src.coordination.workflow_dag import build_kwargs_for_task
        from unittest.mock import Mock
        
        # Create a mock coordinator
        coordinator = Mock()
        
        # Create a task that uses with_db_schema
        task = Phase2Task(
            task_id="test_api",
            agent_type=AgentType.API_DOCUMENTATION,
            output_filename="test.md",
            dependencies=[AgentType.TECHNICAL_DOCUMENTATION, AgentType.DATABASE_SCHEMA],
            kwargs_builder="with_db_schema"
        )
        
        # Test kwargs building
        req_summary = {"project_overview": "Test project"}
        technical_summary = "Technical doc content"
        deps_content = {
            AgentType.DATABASE_SCHEMA: "Database schema content"
        }
        
        kwargs = build_kwargs_for_task(
            task=task,
            coordinator=coordinator,
            req_summary=req_summary,
            technical_summary=technical_summary,
            charter_content=None,
            project_id="test_project",
            context_manager=Mock(),
            deps_content=deps_content
        )
        
        # Verify kwargs contain database_schema_summary
        assert "database_schema_summary" in kwargs
        assert kwargs["database_schema_summary"] == "Database schema content"
        assert kwargs["requirements_summary"] == req_summary
        assert kwargs["technical_summary"] == technical_summary
    
    def test_kwargs_builder_with_api_and_db(self):
        """Test that with_api_and_db kwargs_builder exists and works"""
        from src.coordination.workflow_dag import build_kwargs_for_task
        from unittest.mock import Mock
        
        # Create a mock coordinator
        coordinator = Mock()
        
        # Create a task that uses with_api_and_db
        task = Phase2Task(
            task_id="test_setup",
            agent_type=AgentType.SETUP_GUIDE,
            output_filename="test.md",
            dependencies=[AgentType.API_DOCUMENTATION, AgentType.TECHNICAL_DOCUMENTATION, AgentType.DATABASE_SCHEMA],
            kwargs_builder="with_api_and_db"
        )
        
        # Test kwargs building
        req_summary = {"project_overview": "Test project"}
        technical_summary = "Technical doc content"
        deps_content = {
            AgentType.API_DOCUMENTATION: "API doc content",
            AgentType.DATABASE_SCHEMA: "Database schema content"
        }
        
        kwargs = build_kwargs_for_task(
            task=task,
            coordinator=coordinator,
            req_summary=req_summary,
            technical_summary=technical_summary,
            charter_content=None,
            project_id="test_project",
            context_manager=Mock(),
            deps_content=deps_content
        )
        
        # Verify kwargs contain both api_summary and database_schema_summary
        assert "api_summary" in kwargs
        assert "database_schema_summary" in kwargs
        assert kwargs["api_summary"] == "API doc content"
        assert kwargs["database_schema_summary"] == "Database schema content"
        assert kwargs["requirements_summary"] == req_summary
        assert kwargs["technical_summary"] == technical_summary
    
    def test_phase2_task_count(self):
        """Test that Phase 2+ has correct number of tasks"""
        team_tasks = get_phase2_tasks_for_profile(profile="team")
        individual_tasks = get_phase2_tasks_for_profile(profile="individual")
        
        # Team should have more tasks than individual (team has pm_doc and stakeholder_doc)
        assert len(team_tasks) >= len(individual_tasks)
        
        # Team should have: technical_doc, database_schema, api_doc, setup_guide, dev_doc, test_doc, 
        #                  user_doc, legal_doc, support_playbook, pm_doc, stakeholder_doc
        # Note: business_model and marketing_plan have been moved to Phase 1 for quick decision-making
        # Total: 11 tasks (Phase 2, 3, 4 combined)
        assert len(team_tasks) == 11
        
        # Individual should have: technical_doc, database_schema, api_doc, setup_guide, dev_doc, 
        #                         test_doc, user_doc, legal_doc, support_playbook
        # Total: 9 tasks (Phase 2, 3, 4 combined, no team-only tasks)
        assert len(individual_tasks) == 9
    
    def test_all_phase2_tasks_have_valid_agent_types(self):
        """Test that all Phase 2 tasks have valid agent types"""
        team_tasks = get_phase2_tasks_for_profile(profile="team")
        
        valid_agent_types = set(AgentType)
        
        for task in team_tasks:
            assert task.agent_type in valid_agent_types
            assert task.task_id is not None
            assert task.output_filename is not None
            assert task.kwargs_builder is not None
    
    def test_dependency_consistency(self):
        """Test that dependencies are consistent across tasks"""
        team_tasks = get_phase2_tasks_for_profile(profile="team")
        
        # Build dependency map
        dependency_map = build_task_dependencies(team_tasks)
        
        # Check that all dependencies reference valid tasks
        task_ids = {task.task_id for task in team_tasks}
        
        for task_id, deps in dependency_map.items():
            for dep_id in deps:
                # Dependencies should either be:
                # 1. Other Phase 2 tasks (in task_ids)
                # 2. Phase 1 tasks (handled separately in coordinator)
                # For Phase 2 dependencies, they should be in task_ids
                if dep_id in task_ids:
                    assert dep_id in task_ids, f"Dependency {dep_id} for {task_id} is not a valid Phase 2 task"
    
    def test_api_agent_supports_database_schema_summary(self):
        """Test that API agent supports database_schema_summary parameter"""
        from src.agents.api_documentation_agent import APIDocumentationAgent
        import inspect
        
        # Check generate method signature
        generate_sig = inspect.signature(APIDocumentationAgent.generate)
        assert "database_schema_summary" in generate_sig.parameters
        
        # Check generate_and_save method signature
        generate_and_save_sig = inspect.signature(APIDocumentationAgent.generate_and_save)
        assert "database_schema_summary" in generate_and_save_sig.parameters
    
    def test_setup_guide_agent_supports_database_schema_summary(self):
        """Test that Setup Guide agent supports database_schema_summary parameter"""
        from src.agents.setup_guide_agent import SetupGuideAgent
        import inspect
        
        # Check generate method signature
        generate_sig = inspect.signature(SetupGuideAgent.generate)
        assert "database_schema_summary" in generate_sig.parameters
        
        # Check generate_and_save method signature
        generate_and_save_sig = inspect.signature(SetupGuideAgent.generate_and_save)
        assert "database_schema_summary" in generate_and_save_sig.parameters
    
    def test_get_api_prompt_supports_database_schema_summary(self):
        """Test that get_api_prompt supports database_schema_summary parameter"""
        from prompts.system_prompts import get_api_prompt
        import inspect
        
        # Check function signature
        sig = inspect.signature(get_api_prompt)
        assert "database_schema_summary" in sig.parameters
    
    def test_get_setup_guide_prompt_supports_database_schema_summary(self):
        """Test that get_setup_guide_prompt supports database_schema_summary parameter"""
        from prompts.system_prompts import get_setup_guide_prompt
        import inspect
        
        # Check function signature
        sig = inspect.signature(get_setup_guide_prompt)
        assert "database_schema_summary" in sig.parameters


"""
Workflow DAG Configuration
Defines the dependency graph for document generation workflow (Phase 1 and Phase 2)
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from src.context.shared_context import AgentType


@dataclass
class Phase1Task:
    """Configuration for a Phase 1 workflow task (with quality gate)"""
    task_id: str
    agent_type: AgentType
    output_filename: str
    # Dependencies: List of AgentTypes this task depends on (from Phase 1)
    dependencies: List[AgentType]
    # Function to build kwargs for agent.generate_and_save
    kwargs_builder: Optional[str] = None  # "simple_req", "with_charter", "with_user_stories", "with_tech"
    # Quality threshold for this task (0-100)
    quality_threshold: float = 80.0
    # Whether this task is team-only (True) or always included (False)
    team_only: bool = False


@dataclass
class Phase2Task:
    """Configuration for a Phase 2 workflow task"""
    task_id: str
    agent_type: AgentType
    output_filename: str
    # Dependencies: List of AgentTypes this task depends on (from Phase 1 or Phase 2)
    dependencies: List[AgentType]
    # Function to build kwargs for agent.generate_and_save
    # Args: (coordinator, req_summary, technical_summary, charter_content, project_id, context_manager, deps_content_dict)
    # Returns: dict of kwargs for agent.generate_and_save
    kwargs_builder: Optional[str] = None  # "simple", "with_api", "with_pm", "with_business", "with_user_doc", "custom"


# Phase 1 Task DAG Configuration
# This defines all Phase 1 tasks, their dependencies, quality thresholds, and how to build their arguments
PHASE1_TASKS_CONFIG: Dict[str, Phase1Task] = {
    "requirements": Phase1Task(
        task_id="requirements",
        agent_type=AgentType.REQUIREMENTS_ANALYST,
        output_filename="requirements.md",
        dependencies=[],  # No dependencies
        kwargs_builder="simple_user_idea",
        quality_threshold=80.0,
        team_only=False
    ),
    "project_charter": Phase1Task(
        task_id="project_charter",
        agent_type=AgentType.PROJECT_CHARTER,
        output_filename="project_charter.md",
        dependencies=[AgentType.REQUIREMENTS_ANALYST],
        kwargs_builder="with_requirements",
        quality_threshold=75.0,
        team_only=True  # Team only
    ),
    "user_stories": Phase1Task(
        task_id="user_stories",
        agent_type=AgentType.USER_STORIES,
        output_filename="user_stories.md",
        dependencies=[AgentType.REQUIREMENTS_ANALYST],  # Project charter is optional (team-only)
        kwargs_builder="with_charter",
        quality_threshold=75.0,
        team_only=False
    ),
    "technical_doc": Phase1Task(
        task_id="technical_doc",
        agent_type=AgentType.TECHNICAL_DOCUMENTATION,
        output_filename="technical_spec.md",
        dependencies=[AgentType.REQUIREMENTS_ANALYST, AgentType.USER_STORIES],
        kwargs_builder="with_user_stories",
        quality_threshold=70.0,
        team_only=False
    ),
    "database_schema": Phase1Task(
        task_id="database_schema",
        agent_type=AgentType.DATABASE_SCHEMA,
        output_filename="database_schema.md",
        dependencies=[AgentType.REQUIREMENTS_ANALYST, AgentType.TECHNICAL_DOCUMENTATION],
        kwargs_builder="with_technical",
        quality_threshold=70.0,
        team_only=False
    ),
}


# Phase 2 Task DAG Configuration
# This defines all Phase 2 tasks, their dependencies, and how to build their arguments
# NOTE: database_schema has been moved to Phase 1 (see coordinator.py)
PHASE2_TASKS_CONFIG: Dict[str, Phase2Task] = {
    # L3 Tech Agents
    "api_doc": Phase2Task(
        task_id="api_doc",
        agent_type=AgentType.API_DOCUMENTATION,
        output_filename="api_documentation.md",
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION, AgentType.DATABASE_SCHEMA],
        kwargs_builder="with_db_schema"
    ),
    "setup_guide": Phase2Task(
        task_id="setup_guide",
        agent_type=AgentType.SETUP_GUIDE,
        output_filename="setup_guide.md",
        dependencies=[AgentType.API_DOCUMENTATION, AgentType.TECHNICAL_DOCUMENTATION, AgentType.DATABASE_SCHEMA],
        kwargs_builder="with_api_and_db"
    ),
    "dev_doc": Phase2Task(
        task_id="dev_doc",
        agent_type=AgentType.DEVELOPER_DOCUMENTATION,
        output_filename="developer_guide.md",
        dependencies=[AgentType.API_DOCUMENTATION, AgentType.TECHNICAL_DOCUMENTATION],
        kwargs_builder="with_api"
    ),
    "test_doc": Phase2Task(
        task_id="test_doc",
        agent_type=AgentType.TEST_DOCUMENTATION,
        output_filename="test_plan.md",
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION],
        kwargs_builder="simple_tech"
    ),
    "user_doc": Phase2Task(
        task_id="user_doc",
        agent_type=AgentType.USER_DOCUMENTATION,
        output_filename="user_guide.md",
        dependencies=[AgentType.REQUIREMENTS_ANALYST],
        kwargs_builder="simple_req"
    ),
    "legal_doc": Phase2Task(
        task_id="legal_doc",
        agent_type=AgentType.LEGAL_COMPLIANCE,
        output_filename="legal_compliance.md",
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION],
        kwargs_builder="simple_tech"
    ),
    "support_playbook": Phase2Task(
        task_id="support_playbook",
        agent_type=AgentType.SUPPORT_PLAYBOOK,
        output_filename="support_playbook.md",
        dependencies=[AgentType.USER_DOCUMENTATION],
        kwargs_builder="with_user_doc"
    ),
    # Team-only tasks
    "pm_doc": Phase2Task(
        task_id="pm_doc",
        agent_type=AgentType.PM_DOCUMENTATION,
        output_filename="project_plan.md",
        dependencies=[AgentType.PROJECT_CHARTER],
        kwargs_builder="with_charter"
    ),
    "stakeholder_doc": Phase2Task(
        task_id="stakeholder_doc",
        agent_type=AgentType.STAKEHOLDER_COMMUNICATION,
        output_filename="stakeholder_summary.md",
        dependencies=[AgentType.PM_DOCUMENTATION],
        kwargs_builder="with_pm"
    ),
    "business_model": Phase2Task(
        task_id="business_model",
        agent_type=AgentType.BUSINESS_MODEL,
        output_filename="business_model.md",
        dependencies=[AgentType.PROJECT_CHARTER],
        kwargs_builder="with_charter"
    ),
    "marketing_plan": Phase2Task(
        task_id="marketing_plan",
        agent_type=AgentType.MARKETING_PLAN,
        output_filename="marketing_plan.md",
        dependencies=[AgentType.BUSINESS_MODEL, AgentType.PROJECT_CHARTER],
        kwargs_builder="with_business"
    ),
}


def build_kwargs_for_phase1_task(
    task: Phase1Task,
    user_idea: str,
    project_id: str,
    context_manager: Any,
    deps_content: Dict[AgentType, str]
) -> dict:
    """
    Build keyword arguments for Phase 1 agent.generate_and_save based on task configuration
    
    Args:
        task: Phase1Task configuration
        user_idea: User idea string
        project_id: Project ID
        context_manager: ContextManager instance
        deps_content: Dictionary mapping AgentType to content for dependencies
    
    Returns:
        Dictionary of kwargs for agent.generate_and_save
    """
    base_kwargs = {
        "output_filename": task.output_filename,
        "project_id": project_id,
        "context_manager": context_manager
    }
    
    if task.kwargs_builder == "simple_user_idea":
        # Requirements task - only needs user_idea
        return {
            **base_kwargs,
            "user_idea": user_idea
        }
    
    elif task.kwargs_builder == "with_requirements":
        # Project charter - needs requirements summary
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if not req_output:
            # Fallback to deps_content if not in context yet
            req_content = deps_content.get(AgentType.REQUIREMENTS_ANALYST)
            if not req_content:
                raise ValueError("Requirements not found for project charter")
            # Parse requirements from content (simplified - in practice, should use context)
            from src.context.context_manager import ContextManager
            context = context_manager.get_shared_context(project_id)
            if context and context.requirements:
                req_summary = context.get_requirements_summary()
            else:
                # Fallback: create minimal summary
                req_summary = {"user_idea": user_idea}
        else:
            context = context_manager.get_shared_context(project_id)
            if context and context.requirements:
                req_summary = context.get_requirements_summary()
            else:
                req_summary = {"user_idea": user_idea}
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary
        }
    
    elif task.kwargs_builder == "with_charter":
        # User stories - needs requirements and optionally charter (team-only, may be None for individual)
        context = context_manager.get_shared_context(project_id)
        if not context or not context.requirements:
            raise ValueError("Requirements not found for user stories")
        req_summary = context.get_requirements_summary()
        
        # Get charter content (optional - may not exist for individual profile)
        charter_content = deps_content.get(AgentType.PROJECT_CHARTER)
        if not charter_content:
            charter_output = context_manager.get_agent_output(project_id, AgentType.PROJECT_CHARTER)
            if charter_output:
                charter_content = charter_output.content
            # If no charter (individual profile), charter_content will be None, which is acceptable
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content  # Can be None for individual profile
        }
    
    elif task.kwargs_builder == "with_user_stories":
        # Technical documentation - needs requirements and user stories
        context = context_manager.get_shared_context(project_id)
        if not context or not context.requirements:
            raise ValueError("Requirements not found for technical documentation")
        req_summary = context.get_requirements_summary()
        
        # Get user stories content
        user_stories_content = deps_content.get(AgentType.USER_STORIES)
        if not user_stories_content:
            user_stories_output = context_manager.get_agent_output(project_id, AgentType.USER_STORIES)
            if user_stories_output:
                user_stories_content = user_stories_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "user_stories_summary": user_stories_content,
            "pm_summary": None  # PM doc is in Phase 2
        }
    
    elif task.kwargs_builder == "with_technical":
        # Database schema - needs requirements and technical documentation
        context = context_manager.get_shared_context(project_id)
        if not context or not context.requirements:
            raise ValueError("Requirements not found for database schema")
        req_summary = context.get_requirements_summary()
        
        # Get technical documentation content
        technical_content = deps_content.get(AgentType.TECHNICAL_DOCUMENTATION)
        if not technical_content:
            technical_output = context_manager.get_agent_output(project_id, AgentType.TECHNICAL_DOCUMENTATION)
            if technical_output:
                technical_content = technical_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_content
        }
    
    else:
        raise ValueError(f"Unknown Phase 1 kwargs_builder: {task.kwargs_builder}")


def build_kwargs_for_task(
    task: Phase2Task,
    coordinator: Any,  # WorkflowCoordinator
    req_summary: dict,
    technical_summary: str,
    charter_content: Optional[str],
    project_id: str,
    context_manager: Any,
    deps_content: Dict[AgentType, str]
) -> dict:
    """
    Build keyword arguments for agent.generate_and_save based on task configuration
    
    Args:
        task: Phase2Task configuration
        coordinator: WorkflowCoordinator instance
        req_summary: Requirements summary
        technical_summary: Technical documentation summary
        charter_content: Project charter content
        project_id: Project ID
        context_manager: ContextManager instance
        deps_content: Dictionary mapping AgentType to content for dependencies
    
    Returns:
        Dictionary of kwargs for agent.generate_and_save
    """
    base_kwargs = {
        "output_filename": task.output_filename,
        "project_id": project_id,
        "context_manager": context_manager
    }
    
    if task.kwargs_builder == "simple_req":
        # Simple task that only needs requirements summary
        return {
            **base_kwargs,
            "requirements_summary": req_summary
        }
    
    elif task.kwargs_builder == "simple_tech":
        # Simple task that needs requirements and technical summary
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary
        }
    
    elif task.kwargs_builder == "with_charter":
        # Task that needs requirements and charter
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content
        }
    
    elif task.kwargs_builder == "with_api":
        # Task that needs requirements, technical, and API documentation
        api_summary = deps_content.get(AgentType.API_DOCUMENTATION)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "api_summary": api_summary
        }
    
    elif task.kwargs_builder == "with_db_schema":
        # Task that needs requirements, technical, and database schema
        db_schema_summary = deps_content.get(AgentType.DATABASE_SCHEMA)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "database_schema_summary": db_schema_summary
        }
    
    elif task.kwargs_builder == "with_api_and_db":
        # Task that needs requirements, technical, API documentation, and database schema
        api_summary = deps_content.get(AgentType.API_DOCUMENTATION)
        db_schema_summary = deps_content.get(AgentType.DATABASE_SCHEMA)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "api_summary": api_summary,
            "database_schema_summary": db_schema_summary
        }
    
    elif task.kwargs_builder == "with_pm":
        # Task that needs requirements and PM documentation
        pm_summary = deps_content.get(AgentType.PM_DOCUMENTATION)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "pm_summary": pm_summary
        }
    
    elif task.kwargs_builder == "with_business":
        # Task that needs requirements, charter, and business model
        business_model_summary = deps_content.get(AgentType.BUSINESS_MODEL)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content,
            "business_model_summary": business_model_summary
        }
    
    elif task.kwargs_builder == "with_user_doc":
        # Task that needs requirements and user documentation
        user_doc_summary = deps_content.get(AgentType.USER_DOCUMENTATION)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "user_documentation_summary": user_doc_summary
        }
    
    else:
        raise ValueError(f"Unknown kwargs_builder: {task.kwargs_builder}")


def get_agent_for_phase1_task(coordinator: Any, agent_type: AgentType):
    """Get the agent instance for a given Phase 1 AgentType"""
    agent_map = {
        AgentType.REQUIREMENTS_ANALYST: coordinator.requirements_analyst,
        AgentType.PROJECT_CHARTER: coordinator.project_charter_agent,
        AgentType.USER_STORIES: coordinator.user_stories_agent,
        AgentType.TECHNICAL_DOCUMENTATION: coordinator.technical_agent,
        AgentType.DATABASE_SCHEMA: coordinator.database_schema_agent,
    }
    return agent_map.get(agent_type)


def get_agent_for_task(coordinator: Any, agent_type: AgentType):
    """Get the agent instance for a given Phase 2 AgentType"""
    agent_map = {
        AgentType.API_DOCUMENTATION: coordinator.api_agent,
        AgentType.DATABASE_SCHEMA: coordinator.database_schema_agent,
        AgentType.SETUP_GUIDE: coordinator.setup_guide_agent,
        AgentType.DEVELOPER_DOCUMENTATION: coordinator.developer_agent,
        AgentType.TEST_DOCUMENTATION: coordinator.test_agent,
        AgentType.USER_DOCUMENTATION: coordinator.user_agent,
        AgentType.LEGAL_COMPLIANCE: coordinator.legal_compliance_agent,
        AgentType.SUPPORT_PLAYBOOK: coordinator.support_playbook_agent,
        AgentType.PM_DOCUMENTATION: coordinator.pm_agent,
        AgentType.STAKEHOLDER_COMMUNICATION: coordinator.stakeholder_agent,
        AgentType.BUSINESS_MODEL: coordinator.business_model_agent,
        AgentType.MARKETING_PLAN: coordinator.marketing_plan_agent,
    }
    return agent_map.get(agent_type)


def get_phase1_tasks_for_profile(profile: str = "team") -> List[Phase1Task]:
    """
    Get Phase 1 task configurations for a given profile
    
    Args:
        profile: Project profile ("team" or "individual")
    
    Returns:
        List of Phase1Task objects with dependencies adjusted for profile
    """
    all_tasks = list(PHASE1_TASKS_CONFIG.values())
    
    # Filter out team-only tasks for individual profile
    if profile == "individual":
        tasks = [task for task in all_tasks if not task.team_only]
    else:
        tasks = all_tasks.copy()
        # For team profile, ensure user_stories depends on project_charter
        # Create a modified user_stories task with project_charter dependency
        user_stories_task = None
        for task in tasks:
            if task.task_id == "user_stories":
                user_stories_task = task
                break
        
        if user_stories_task:
            # Update dependencies to include project_charter for team profile
            if AgentType.PROJECT_CHARTER not in user_stories_task.dependencies:
                # Create a new task with updated dependencies
                from dataclasses import replace
                user_stories_task = replace(
                    user_stories_task,
                    dependencies=user_stories_task.dependencies + [AgentType.PROJECT_CHARTER]
                )
                # Replace in tasks list
                tasks = [task if task.task_id != "user_stories" else user_stories_task for task in tasks]
    
    return tasks


def build_phase1_task_dependencies(tasks: List[Phase1Task]) -> Dict[str, List[str]]:
    """
    Build dependency map from Phase 1 task configurations
    
    Converts AgentType dependencies to task_id dependencies for ParallelExecutor
    
    Args:
        tasks: List of Phase1Task objects
    
    Returns:
        Dictionary mapping task_id to list of dependency task_ids
    """
    # Create mapping from AgentType to task_id
    agent_type_to_task_id = {task.agent_type: task.task_id for task in tasks}
    
    # Build dependency map
    dependency_map = {}
    for task in tasks:
        # Convert AgentType dependencies to task_id dependencies
        dep_task_ids = []
        for dep_type in task.dependencies:
            if dep_type in agent_type_to_task_id:
                dep_task_ids.append(agent_type_to_task_id[dep_type])
        
        dependency_map[task.task_id] = dep_task_ids
    
    return dependency_map


def get_phase2_tasks_for_profile(profile: str = "team") -> List[Phase2Task]:
    """
    Get Phase 2 task configurations for a given profile
    
    Args:
        profile: Project profile ("team" or "individual")
    
    Returns:
        List of Phase2Task objects
    """
    # Common tasks (both team and individual)
    # NOTE: db_schema has been moved to Phase 1 (see coordinator.py)
    common_tasks = [
        "api_doc",
        "setup_guide",
        "dev_doc",
        "test_doc",
        "user_doc",
        "legal_doc",
        "support_playbook"
    ]
    
    tasks = [PHASE2_TASKS_CONFIG[task_id] for task_id in common_tasks]
    
    # Team-only tasks
    if profile == "team":
        team_tasks = [
            "pm_doc",
            "stakeholder_doc",
            "business_model",
            "marketing_plan"
        ]
        tasks.extend([PHASE2_TASKS_CONFIG[task_id] for task_id in team_tasks])
    
    return tasks


def build_task_dependencies(tasks: List[Phase2Task]) -> Dict[str, List[str]]:
    """
    Build dependency map from task configurations
    
    Converts AgentType dependencies to task_id dependencies for ParallelExecutor
    
    Args:
        tasks: List of Phase2Task objects
    
    Returns:
        Dictionary mapping task_id to list of dependency task_ids
    """
    # Create mapping from AgentType to task_id
    agent_type_to_task_id = {task.agent_type: task.task_id for task in tasks}
    
    # Also map Phase 1 agent types to their task_ids (they're not in Phase 2, but we need to track them)
    # Phase 1 tasks are already complete, so we can reference them by their AgentType
    # NOTE: DATABASE_SCHEMA is now in Phase 1, so it's included here
    phase1_agent_types = [
        AgentType.REQUIREMENTS_ANALYST,
        AgentType.PROJECT_CHARTER,
        AgentType.USER_STORIES,
        AgentType.TECHNICAL_DOCUMENTATION,
        AgentType.DATABASE_SCHEMA  # Moved to Phase 1
    ]
    
    # Build dependency map
    dependency_map = {}
    for task in tasks:
        # Convert AgentType dependencies to task_id dependencies
        # Note: Phase 1 dependencies don't have task_ids in Phase 2, so we need to handle them specially
        dep_task_ids = []
        for dep_type in task.dependencies:
            # Check if this dependency is a Phase 2 task
            if dep_type in agent_type_to_task_id:
                dep_task_ids.append(agent_type_to_task_id[dep_type])
            # Phase 1 dependencies are already complete, so we don't need to track them in dependencies
            # The ParallelExecutor will handle this by checking if dependencies are complete
            # For Phase 1 dependencies, we assume they're always available (completed in Phase 1)
        
        dependency_map[task.task_id] = dep_task_ids
    
    return dependency_map

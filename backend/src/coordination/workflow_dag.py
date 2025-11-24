"""
Workflow DAG Configuration
Defines the dependency graph for document generation workflow (Phase 1 and Phase 2)
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from src.context.shared_context import AgentType


@dataclass
class WorkflowTask:
    """
    Unified configuration for all workflow tasks (Phase 1-5)
    
    This dataclass supports all phases of the workflow:
    - Phase 1: Strategic & Business Foundation (requires approval, has quality gates)
    - Phase 2: Technical Documentation & Implementation
    - Phase 3: Development & Testing
    - Phase 4: User & Support
    - Phase 5: (Currently empty - management documents moved to Phase 1)
    """
    task_id: str
    agent_type: AgentType
    output_filename: str
    # Phase number: 1, 2, 3, 4, or 5 - determines which phase this task belongs to
    phase_number: int
    # Dependencies: List of AgentTypes this task depends on (from Phase 1 or previous phases)
    dependencies: List[AgentType]
    # Function to build kwargs for agent.generate_and_save
    kwargs_builder: Optional[str] = None
    # Quality threshold for this task (0-100) - mainly used in Phase 1
    quality_threshold: Optional[float] = None
    # Whether this task is team-only (True) or always included (False) - mainly used in Phase 1
    team_only: bool = False


# Backward compatibility aliases (deprecated, use WorkflowTask instead)
Phase1Task = WorkflowTask  # Alias for backward compatibility
Phase2Task = WorkflowTask  # Alias for backward compatibility


# Unified Workflow Task DAG Configuration
# All tasks for all phases (1-5) are defined here
# Tasks are organized by phase number for sequential execution
# NOTE: Phase 1 (requirements, project_charter, user_stories, business_model, marketing_plan, pm_doc, stakeholder_doc) requires user approval before proceeding
WORKFLOW_TASKS_CONFIG: Dict[str, WorkflowTask] = {
    # ========== PHASE 1: Strategic & Business Foundation Documents (REQUIRES USER APPROVAL) ==========
    # These are the strategic and business documents that define the project foundation.
    # After Phase 1 completes, the workflow pauses for user review and approval.
    "requirements": WorkflowTask(
        task_id="requirements",
        agent_type=AgentType.REQUIREMENTS_ANALYST,
        output_filename="requirements.md",
        phase_number=1,
        dependencies=[],  # No dependencies
        kwargs_builder="simple_user_idea",
        quality_threshold=80.0,
        team_only=False
    ),
    "project_charter": WorkflowTask(
        task_id="project_charter",
        agent_type=AgentType.PROJECT_CHARTER,
        output_filename="project_charter.md",
        phase_number=1,
        dependencies=[AgentType.REQUIREMENTS_ANALYST],
        kwargs_builder="with_requirements",
        quality_threshold=80.0,
        team_only=True
    ),
    "user_stories": WorkflowTask(
        task_id="user_stories",
        agent_type=AgentType.USER_STORIES,
        output_filename="user_stories.md",
        phase_number=1,
        dependencies=[AgentType.REQUIREMENTS_ANALYST, AgentType.PROJECT_CHARTER],
        kwargs_builder="with_charter",
        quality_threshold=80.0,
        team_only=True
    ),
    "business_model": WorkflowTask(
        task_id="business_model",
        agent_type=AgentType.BUSINESS_MODEL,
        output_filename="business_model.md",
        phase_number=1,
        dependencies=[AgentType.PROJECT_CHARTER],
        kwargs_builder="with_charter",
        quality_threshold=80.0,
        team_only=True
    ),
    "marketing_plan": WorkflowTask(
        task_id="marketing_plan",
        agent_type=AgentType.MARKETING_PLAN,
        output_filename="marketing_plan.md",
        phase_number=1,
        dependencies=[AgentType.BUSINESS_MODEL, AgentType.PROJECT_CHARTER],
        kwargs_builder="with_business",
        quality_threshold=80.0,
        team_only=True
    ),
    "pm_doc": WorkflowTask(
        task_id="pm_doc",
        agent_type=AgentType.PM_DOCUMENTATION,
        output_filename="project_plan.md",
        phase_number=1,
        dependencies=[AgentType.PROJECT_CHARTER],
        kwargs_builder="with_charter",
        quality_threshold=80.0,
        team_only=True
    ),
    "stakeholder_doc": WorkflowTask(
        task_id="stakeholder_doc",
        agent_type=AgentType.STAKEHOLDER_COMMUNICATION,
        output_filename="stakeholder_summary.md",
        phase_number=1,
        dependencies=[AgentType.PM_DOCUMENTATION],
        kwargs_builder="with_pm",
        quality_threshold=80.0,
        team_only=True
    ),
    "wbs": WorkflowTask(
        task_id="wbs",
        agent_type=AgentType.WBS_AGENT,
        output_filename="work_breakdown_structure.md",
        phase_number=1,
        dependencies=[AgentType.PM_DOCUMENTATION, AgentType.PROJECT_CHARTER],
        kwargs_builder="with_pm",
        quality_threshold=80.0,
        team_only=True
    ),
    # ========== PHASE 2: Technical Documentation ==========
    # Technical specification document that builds on Phase 1 foundation
    "technical_doc": WorkflowTask(
        task_id="technical_doc",
        agent_type=AgentType.TECHNICAL_DOCUMENTATION,
        output_filename="technical_spec.md",
        phase_number=2,
        dependencies=[AgentType.REQUIREMENTS_ANALYST, AgentType.USER_STORIES],
        kwargs_builder="with_user_stories",  # Will use requirements if user_stories not available
        quality_threshold=80.0,
        team_only=False
    ),
    # ========== PHASE 2 (continued): Technical Implementation Documents ==========
    # These documents build on the technical specification
    "database_schema": WorkflowTask(
        task_id="database_schema",
        agent_type=AgentType.DATABASE_SCHEMA,
        output_filename="database_schema.md",
        phase_number=2,
        dependencies=[AgentType.REQUIREMENTS_ANALYST, AgentType.TECHNICAL_DOCUMENTATION],
        kwargs_builder="with_technical"
    ),
    # ========== PHASE 2 (continued): API and Setup Documents ==========
    "api_doc": WorkflowTask(
        task_id="api_doc",
        agent_type=AgentType.API_DOCUMENTATION,
        output_filename="api_documentation.md",
        phase_number=2,
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION, AgentType.DATABASE_SCHEMA, AgentType.USER_STORIES],
        kwargs_builder="with_db_schema_and_user_stories"
    ),
    "setup_guide": WorkflowTask(
        task_id="setup_guide",
        agent_type=AgentType.SETUP_GUIDE,
        output_filename="setup_guide.md",
        phase_number=2,
        dependencies=[AgentType.API_DOCUMENTATION, AgentType.TECHNICAL_DOCUMENTATION, AgentType.DATABASE_SCHEMA],
        kwargs_builder="with_api_and_db"
    ),
    # ========== PHASE 3: Development & Testing Documents ==========
    "dev_doc": WorkflowTask(
        task_id="dev_doc",
        agent_type=AgentType.DEVELOPER_DOCUMENTATION,
        output_filename="developer_guide.md",
        phase_number=3,
        dependencies=[AgentType.API_DOCUMENTATION, AgentType.TECHNICAL_DOCUMENTATION],
        kwargs_builder="with_api"
    ),
    "test_doc": WorkflowTask(
        task_id="test_doc",
        agent_type=AgentType.TEST_DOCUMENTATION,
        output_filename="test_plan.md",
        phase_number=3,
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION, AgentType.API_DOCUMENTATION, AgentType.DATABASE_SCHEMA, AgentType.USER_STORIES],
        kwargs_builder="for_test"
    ),
    # ========== PHASE 4: User & Support Documents ==========
    "user_doc": WorkflowTask(
        task_id="user_doc",
        agent_type=AgentType.USER_DOCUMENTATION,
        output_filename="user_guide.md",
        phase_number=4,
        dependencies=[AgentType.REQUIREMENTS_ANALYST],
        kwargs_builder="simple_req"
    ),
    "support_playbook": WorkflowTask(
        task_id="support_playbook",
        agent_type=AgentType.SUPPORT_PLAYBOOK,
        output_filename="support_playbook.md",
        phase_number=4,
        dependencies=[AgentType.USER_DOCUMENTATION],
        kwargs_builder="with_user_doc"
    ),
    "legal_doc": WorkflowTask(
        task_id="legal_doc",
        agent_type=AgentType.LEGAL_COMPLIANCE,
        output_filename="legal_compliance.md",
        phase_number=4,
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION],
        kwargs_builder="simple_tech"
    ),
    # ========== PHASE 5: (Empty - all management documents moved to Phase 1) ==========
    # Note: PM Documentation and Stakeholder Communication have been moved to Phase 1
    # as they are strategic foundation documents
}

# Backward compatibility: Keep old config names for existing code
PHASE1_TASKS_CONFIG: Dict[str, WorkflowTask] = {
    k: v for k, v in WORKFLOW_TASKS_CONFIG.items() if v.phase_number == 1
}

PHASE2_TASKS_CONFIG: Dict[str, WorkflowTask] = {
    k: v for k, v in WORKFLOW_TASKS_CONFIG.items() if v.phase_number >= 2
}


def build_kwargs_for_phase1_task(
    task: WorkflowTask,
    user_idea: str,
    project_id: str,
    context_manager: Any,
    deps_content: Dict[AgentType, str],
    code_analysis_summary: Optional[str] = None
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
        # Project charter - needs requirements summary AND full requirements document content
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        context = context_manager.get_shared_context(project_id)
        
        if context and context.requirements:
            req_summary = context.get_requirements_summary()
            # Always include the original user_idea in the summary for better context
            if not req_summary.get("user_idea") or req_summary.get("user_idea") != user_idea:
                req_summary["user_idea"] = user_idea
        else:
            # Fallback: create summary from user_idea
            req_summary = {"user_idea": user_idea}
        
        # Also include full requirements document content if available (for better context)
        if req_output and req_output.content:
            req_summary["requirements_document"] = req_output.content  # Full requirements document
        
        # Ensure user_idea is always present
        if "user_idea" not in req_summary or not req_summary["user_idea"]:
            req_summary["user_idea"] = user_idea
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary
        }
    
    elif task.kwargs_builder == "with_charter":
        # User stories, business_model, pm_doc - needs requirements and optionally charter (team-only, may be None for individual)
        context = context_manager.get_shared_context(project_id)
        if not context or not context.requirements:
            raise ValueError("Requirements not found")
        req_summary = context.get_requirements_summary()
        
        # Always include the original user_idea in the summary for better context
        if not req_summary.get("user_idea") or req_summary.get("user_idea") != user_idea:
            req_summary["user_idea"] = user_idea
        
        # Also include full requirements document content if available (for better context)
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content:
            req_summary["requirements_document"] = req_output.content  # Full requirements document
        
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
    
    elif task.kwargs_builder == "with_business":
        # Marketing plan - needs requirements, charter, and business model
        context = context_manager.get_shared_context(project_id)
        if not context or not context.requirements:
            raise ValueError("Requirements not found for marketing plan")
        req_summary = context.get_requirements_summary()
        
        # Always include the original user_idea in the summary for better context
        if not req_summary.get("user_idea") or req_summary.get("user_idea") != user_idea:
            req_summary["user_idea"] = user_idea
        
        # Also include full requirements document content if available (for better context)
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content:
            req_summary["requirements_document"] = req_output.content  # Full requirements document
        
        # Get charter content
        charter_content = deps_content.get(AgentType.PROJECT_CHARTER)
        if not charter_content:
            charter_output = context_manager.get_agent_output(project_id, AgentType.PROJECT_CHARTER)
            if charter_output:
                charter_content = charter_output.content
        
        # Get business model content
        business_model_content = deps_content.get(AgentType.BUSINESS_MODEL)
        if not business_model_content:
            business_output = context_manager.get_agent_output(project_id, AgentType.BUSINESS_MODEL)
            if business_output:
                business_model_content = business_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content,
            "business_model_summary": business_model_content
        }
    
    elif task.kwargs_builder == "with_pm":
        # Stakeholder communication, WBS - needs requirements, charter, and PM documentation
        context = context_manager.get_shared_context(project_id)
        if not context or not context.requirements:
            raise ValueError("Requirements not found")
        req_summary = context.get_requirements_summary()
        
        # Always include the original user_idea in the summary for better context
        if not req_summary.get("user_idea") or req_summary.get("user_idea") != user_idea:
            req_summary["user_idea"] = user_idea
        
        # Also include full requirements document content if available (for better context)
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content:
            req_summary["requirements_document"] = req_output.content  # Full requirements document
        
        # Get charter content (optional - may not exist for individual profile)
        charter_content = deps_content.get(AgentType.PROJECT_CHARTER)
        if not charter_content:
            charter_output = context_manager.get_agent_output(project_id, AgentType.PROJECT_CHARTER)
            if charter_output:
                charter_content = charter_output.content
        
        # Get PM documentation content
        pm_summary = deps_content.get(AgentType.PM_DOCUMENTATION)
        if not pm_summary:
            pm_output = context_manager.get_agent_output(project_id, AgentType.PM_DOCUMENTATION)
            if pm_output:
                pm_summary = pm_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content,  # Can be None for individual profile
            "pm_summary": pm_summary
        }
    
    else:
        raise ValueError(f"Unknown Phase 1 kwargs_builder: {task.kwargs_builder}")


def build_kwargs_for_task(
    task: WorkflowTask,
    coordinator: Any,  # WorkflowCoordinator
    req_summary: dict,
    technical_summary: str,
    charter_content: Optional[str],
    project_id: str,
    context_manager: Any,
    deps_content: Dict[AgentType, str],
    code_analysis_summary: Optional[str] = None
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
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary
        }
    
    elif task.kwargs_builder == "simple_tech":
        # Simple task that needs requirements and technical summary
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary
        }
    
    elif task.kwargs_builder == "with_charter":
        # Task that needs requirements and charter
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content
        }
    
    elif task.kwargs_builder == "with_api":
        # Task that needs requirements, technical, and API documentation
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        api_summary = deps_content.get(AgentType.API_DOCUMENTATION)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "api_summary": api_summary
        }
    
    elif task.kwargs_builder == "with_db_schema":
        # Task that needs requirements, technical, and database schema
        # In code-first mode, also uses code_analysis_summary
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        db_schema_summary = deps_content.get(AgentType.DATABASE_SCHEMA)
        kwargs = {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "database_schema_summary": db_schema_summary
        }
        
        # Add code analysis summary if available (code-first mode)
        if code_analysis_summary:
            kwargs["code_analysis_summary"] = code_analysis_summary
        
        return kwargs
    
    elif task.kwargs_builder == "with_db_schema_and_user_stories":
        # API Documentation - needs requirements, technical, database schema, and user stories
        # In code-first mode, also uses code_analysis_summary
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        # Get database schema content
        db_schema_summary = deps_content.get(AgentType.DATABASE_SCHEMA)
        if not db_schema_summary:
            db_schema_output = context_manager.get_agent_output(project_id, AgentType.DATABASE_SCHEMA)
            if db_schema_output:
                db_schema_summary = db_schema_output.content
        
        # Get user stories content (required for API design)
        user_stories_summary = deps_content.get(AgentType.USER_STORIES)
        if not user_stories_summary:
            user_stories_output = context_manager.get_agent_output(project_id, AgentType.USER_STORIES)
            if user_stories_output:
                user_stories_summary = user_stories_output.content
        
        kwargs = {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "database_schema_summary": db_schema_summary,
            "user_stories_summary": user_stories_summary  # Add user stories for API design
        }
        
        # Add code analysis summary if available (code-first mode)
        if code_analysis_summary:
            kwargs["code_analysis_summary"] = code_analysis_summary
        
        return kwargs
    
    elif task.kwargs_builder == "with_api_and_db":
        # Task that needs requirements, technical, API documentation, and database schema
        # In code-first mode, also uses code_analysis_summary
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        api_summary = deps_content.get(AgentType.API_DOCUMENTATION)
        db_schema_summary = deps_content.get(AgentType.DATABASE_SCHEMA)
        kwargs = {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "api_summary": api_summary,
            "database_schema_summary": db_schema_summary
        }
        
        # Add code analysis summary if available (code-first mode)
        if code_analysis_summary:
            kwargs["code_analysis_summary"] = code_analysis_summary
        
        return kwargs
    
    elif task.kwargs_builder == "for_test":
        # Test Documentation - needs requirements, technical, API documentation, database schema, and user stories
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        # Get API documentation content (required for API endpoint testing)
        api_summary = deps_content.get(AgentType.API_DOCUMENTATION)
        if not api_summary:
            api_output = context_manager.get_agent_output(project_id, AgentType.API_DOCUMENTATION)
            if api_output:
                api_summary = api_output.content
        
        # Get database schema content (required for database operation testing)
        db_schema_summary = deps_content.get(AgentType.DATABASE_SCHEMA)
        if not db_schema_summary:
            db_schema_output = context_manager.get_agent_output(project_id, AgentType.DATABASE_SCHEMA)
            if db_schema_output:
                db_schema_summary = db_schema_output.content
        
        # Get user stories content (required for user story testing)
        user_stories_summary = deps_content.get(AgentType.USER_STORIES)
        if not user_stories_summary:
            user_stories_output = context_manager.get_agent_output(project_id, AgentType.USER_STORIES)
            if user_stories_output:
                user_stories_summary = user_stories_output.content
        
        kwargs = {
            **base_kwargs,
            "requirements_summary": req_summary,
            "technical_summary": technical_summary,
            "api_summary": api_summary,  # For API endpoint testing
            "database_schema_summary": db_schema_summary,  # For database operation testing
            "user_stories_summary": user_stories_summary  # For user story testing
        }
        
        return kwargs
    
    elif task.kwargs_builder == "with_pm":
        # Task that needs requirements, charter, and PM documentation (e.g., WBS, stakeholder_doc)
        context = context_manager.get_shared_context(project_id)
        if not context or not context.requirements:
            raise ValueError("Requirements not found")
        req_summary = context.get_requirements_summary()
        
        # Always include the original user_idea in the summary for better context
        # Note: user_idea might not be available in build_kwargs_for_task, so we'll get it from requirements
        if not req_summary.get("user_idea"):
            # Try to get user_idea from requirements if available
            if context.requirements and context.requirements.user_idea:
                req_summary["user_idea"] = context.requirements.user_idea
        
        # Also include full requirements document content if available (for better context)
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content:
            req_summary["requirements_document"] = req_output.content  # Full requirements document
        
        # Get charter content (optional - may not exist for individual profile)
        charter_content = deps_content.get(AgentType.PROJECT_CHARTER)
        if not charter_content:
            charter_output = context_manager.get_agent_output(project_id, AgentType.PROJECT_CHARTER)
            if charter_output:
                charter_content = charter_output.content
        
        # Get PM documentation content
        pm_summary = deps_content.get(AgentType.PM_DOCUMENTATION)
        if not pm_summary:
            pm_output = context_manager.get_agent_output(project_id, AgentType.PM_DOCUMENTATION)
            if pm_output:
                pm_summary = pm_output.content
        
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content,  # Can be None for individual profile
            "pm_summary": pm_summary
        }
    
    elif task.kwargs_builder == "with_business":
        # Task that needs requirements, charter, and business model
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        business_model_summary = deps_content.get(AgentType.BUSINESS_MODEL)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "project_charter_summary": charter_content,
            "business_model_summary": business_model_summary
        }
    
    elif task.kwargs_builder == "with_user_doc":
        # Task that needs requirements and user documentation
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        user_doc_summary = deps_content.get(AgentType.USER_DOCUMENTATION)
        return {
            **base_kwargs,
            "requirements_summary": req_summary,
            "user_documentation_summary": user_doc_summary
        }
    
    elif task.kwargs_builder == "with_user_stories":
        # Technical documentation - needs requirements and optionally user stories
        # In code-first mode, also uses code_analysis_summary
        # Ensure requirements_summary includes full requirements document
        req_output = context_manager.get_agent_output(project_id, AgentType.REQUIREMENTS_ANALYST)
        if req_output and req_output.content and "requirements_document" not in req_summary:
            req_summary["requirements_document"] = req_output.content
        
        # Get user stories content (optional - may not exist in Phase 1)
        user_stories_content = deps_content.get(AgentType.USER_STORIES)
        if not user_stories_content:
            user_stories_output = context_manager.get_agent_output(project_id, AgentType.USER_STORIES)
            if user_stories_output:
                user_stories_content = user_stories_output.content
        
        kwargs = {
            **base_kwargs,
            "requirements_summary": req_summary,
            "user_stories_summary": user_stories_content,  # Can be None if not available
            "pm_summary": None
        }
        
        # Add code analysis summary if available (code-first mode)
        if code_analysis_summary:
            kwargs["code_analysis_summary"] = code_analysis_summary
        
        return kwargs
    
    elif task.kwargs_builder == "with_technical":
        # Database schema - needs requirements and technical documentation
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
        raise ValueError(f"Unknown kwargs_builder: {task.kwargs_builder}")


def get_agent_for_phase1_task(coordinator: Any, agent_type: AgentType):
    """Get the agent instance for a given Phase 1 AgentType"""
    agent_map = {
        AgentType.REQUIREMENTS_ANALYST: coordinator.requirements_analyst,
        AgentType.PROJECT_CHARTER: coordinator.project_charter_agent,
        AgentType.USER_STORIES: coordinator.user_stories_agent,
        AgentType.BUSINESS_MODEL: coordinator.business_model_agent,
        AgentType.MARKETING_PLAN: coordinator.marketing_plan_agent,
        AgentType.PM_DOCUMENTATION: coordinator.pm_agent,
        AgentType.STAKEHOLDER_COMMUNICATION: coordinator.stakeholder_agent,
        AgentType.WBS_AGENT: coordinator.wbs_agent,
        AgentType.TECHNICAL_DOCUMENTATION: coordinator.technical_agent,
    }
    return agent_map.get(agent_type)


def get_agent_for_task(coordinator: Any, agent_type: AgentType):
    """Get the agent instance for a given Phase 2+ AgentType"""
    agent_map = {
        AgentType.DATABASE_SCHEMA: coordinator.database_schema_agent,
        AgentType.API_DOCUMENTATION: coordinator.api_agent,
        AgentType.SETUP_GUIDE: coordinator.setup_guide_agent,
        AgentType.DEVELOPER_DOCUMENTATION: coordinator.developer_agent,
        AgentType.TEST_DOCUMENTATION: coordinator.test_agent,
        AgentType.USER_DOCUMENTATION: coordinator.user_agent,
        AgentType.LEGAL_COMPLIANCE: coordinator.legal_compliance_agent,
        AgentType.SUPPORT_PLAYBOOK: coordinator.support_playbook_agent,
        AgentType.PROJECT_CHARTER: coordinator.project_charter_agent,
        AgentType.USER_STORIES: coordinator.user_stories_agent,
        AgentType.BUSINESS_MODEL: coordinator.business_model_agent,
        AgentType.MARKETING_PLAN: coordinator.marketing_plan_agent,
        AgentType.PM_DOCUMENTATION: coordinator.pm_agent,
        AgentType.STAKEHOLDER_COMMUNICATION: coordinator.stakeholder_agent,
    }
    return agent_map.get(agent_type)


def get_phase1_tasks_for_profile(profile: str = "team") -> List[WorkflowTask]:
    """
    Get Phase 1 task configurations for a given profile
    
    Args:
        profile: Project profile ("team" or "individual")
    
    Returns:
        List of WorkflowTask objects for Phase 1 with dependencies adjusted for profile
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


def build_phase1_task_dependencies(tasks: List[WorkflowTask]) -> Dict[str, List[str]]:
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


def get_phase2_tasks_for_profile(profile: str = "team") -> List[WorkflowTask]:
    """
    Get all Phase 2+ task configurations for a given profile (backward compatibility)
    
    Args:
        profile: Project profile ("team" or "individual")
    
    Returns:
        List of WorkflowTask objects for all phases 2-5
    """
    return get_tasks_for_phases(profile=profile, phases=[2, 3, 4, 5])


def get_tasks_for_phases(profile: str = "team", phases: List[int] = None) -> List[WorkflowTask]:
    """
    Get task configurations for specific phases
    
    Args:
        profile: Project profile ("team" or "individual")
        phases: List of phase numbers to include (e.g., [2, 3] for Phase 2 and 3)
                If None, returns all phases (2-4)
    
    Returns:
        List of WorkflowTask objects for the specified phases
    """
    if phases is None:
        phases = get_available_phases(profile=profile)
    
    # Get all tasks for the specified phases
    all_tasks = [task for task in PHASE2_TASKS_CONFIG.values() if task.phase_number in phases]
    
    # Filter by profile
    if profile == "individual":
        # Individual profile: exclude tasks that depend on team-only Phase 1 tasks
        # PROJECT_CHARTER is team-only, so exclude tasks that depend on it
        # Also exclude tasks that depend on PM_DOCUMENTATION (which depends on PROJECT_CHARTER)
        team_only_deps = {AgentType.PROJECT_CHARTER, AgentType.PM_DOCUMENTATION}
        tasks = [
            task for task in all_tasks
            if not any(dep in team_only_deps for dep in task.dependencies)
        ]
    else:
        tasks = all_tasks
    
    return tasks


def get_tasks_for_phase(profile: str = "team", phase_number: int = 2) -> List[WorkflowTask]:
    """
    Get task configurations for a specific phase
    
    Args:
        profile: Project profile ("team" or "individual")
        phase_number: Phase number (2, 3, 4, or 5)
    
    Returns:
        List of WorkflowTask objects for the specified phase
    """
    return get_tasks_for_phases(profile=profile, phases=[phase_number])


def get_available_phases(profile: str = "team") -> List[int]:
    """
    Get list of available phase numbers for a given profile
    
    Args:
        profile: Project profile ("team" or "individual")
    
    Returns:
        List of available phase numbers (Phase 2, 3, 4, 5)
        Note: Phase 1 is always executed first and requires approval
    """
    # Phase structure:
    # Phase 1: Strategic & Business Foundation (requirements, project_charter, user_stories, business_model, marketing_plan, pm_doc, stakeholder_doc) - requires approval
    # Phase 2: Technical Documentation (technical_doc, database, API, setup)
    # Phase 3: Development & Testing (dev_doc, test_doc)
    # Phase 4: User & Support (user_doc, support_playbook, legal)
    # Phase 5: (Empty - all management documents moved to Phase 1)
    return [2, 3, 4]


def build_task_dependencies(tasks: List[WorkflowTask]) -> Dict[str, List[str]]:
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
    
    # Build dependency map
    # Note: Phase 1 dependencies (REQUIREMENTS_ANALYST, TECHNICAL_DOCUMENTATION) are already complete
    # and don't have task_ids in Phase 2+, so we handle them specially in the dependency resolution
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

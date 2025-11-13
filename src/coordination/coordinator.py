"""
Workflow Coordinator
Orchestrates multi-agent documentation generation workflow
"""
from typing import Optional, Dict, List, Callable
from datetime import datetime
from pathlib import Path
import uuid
import os
import re

from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, SharedContext, AgentOutput
from src.utils.logger import get_logger
from src.config.settings import get_settings, get_environment

logger = get_logger(__name__)
from src.agents.requirements_analyst import RequirementsAnalyst
from src.agents.pm_documentation_agent import PMDocumentationAgent
from src.agents.technical_documentation_agent import TechnicalDocumentationAgent
from src.agents.api_documentation_agent import APIDocumentationAgent
from src.agents.developer_documentation_agent import DeveloperDocumentationAgent
from src.agents.stakeholder_communication_agent import StakeholderCommunicationAgent
from src.agents.user_documentation_agent import UserDocumentationAgent
from src.agents.test_documentation_agent import TestDocumentationAgent
from src.agents.quality_reviewer_agent import QualityReviewerAgent
from src.agents.format_converter_agent import FormatConverterAgent
from src.agents.claude_cli_documentation_agent import ClaudeCLIDocumentationAgent
from src.agents.project_charter_agent import ProjectCharterAgent
from src.agents.user_stories_agent import UserStoriesAgent
from src.agents.database_schema_agent import DatabaseSchemaAgent
from src.agents.setup_guide_agent import SetupGuideAgent
from src.agents.marketing_plan_agent import MarketingPlanAgent
from src.agents.business_model_agent import BusinessModelAgent
from src.agents.support_playbook_agent import SupportPlaybookAgent
from src.agents.legal_compliance_agent import LegalComplianceAgent
from src.agents.document_improver_agent import DocumentImproverAgent
from src.agents.code_analyst_agent import CodeAnalystAgent
from src.agents.wbs_agent import WBSAgent
from src.utils.file_manager import FileManager
from src.utils.cross_referencer import CrossReferencer
from src.utils.parallel_executor import ParallelExecutor, TaskStatus
from src.utils.async_parallel_executor import AsyncParallelExecutor, TaskStatus as AsyncTaskStatus
from src.rate_limit.queue_manager import RequestQueue
from src.utils.document_organizer import format_documents_by_level, get_documents_summary, get_document_level, get_document_display_name
from src.coordination.workflow_dag import (
    get_phase1_tasks_for_profile,
    get_phase2_tasks_for_profile,
    get_tasks_for_phases,
    get_tasks_for_phase,
    WorkflowTask,
    get_available_phases,
    build_phase1_task_dependencies,
    build_task_dependencies,
    build_kwargs_for_phase1_task,
    build_kwargs_for_task,
    get_agent_for_phase1_task,
    get_agent_for_task,
    Phase1Task,
    Phase2Task
)

import asyncio

# Mapping from AgentType to folder name for file organization
AGENT_TYPE_TO_FOLDER = {
    AgentType.REQUIREMENTS_ANALYST: "requirements",
    AgentType.PROJECT_CHARTER: "charter",
    AgentType.USER_STORIES: "user_stories",
    AgentType.TECHNICAL_DOCUMENTATION: "technical",
    AgentType.DATABASE_SCHEMA: "database",
    AgentType.API_DOCUMENTATION: "api",
    AgentType.SETUP_GUIDE: "setup",
    AgentType.DEVELOPER_DOCUMENTATION: "developer",
    AgentType.TEST_DOCUMENTATION: "test",
    AgentType.USER_DOCUMENTATION: "user",
    AgentType.LEGAL_COMPLIANCE: "legal",
    AgentType.SUPPORT_PLAYBOOK: "support",
    AgentType.PM_DOCUMENTATION: "pm",
    AgentType.STAKEHOLDER_COMMUNICATION: "stakeholder",
    AgentType.BUSINESS_MODEL: "business",
    AgentType.MARKETING_PLAN: "marketing",
    AgentType.WBS_AGENT: "pm",
    AgentType.QUALITY_REVIEWER: "quality",
}

# Mapping from AgentType to doc_type for results storage (Phase 1)
AGENT_TYPE_TO_DOC_TYPE_PHASE1 = {
    AgentType.REQUIREMENTS_ANALYST: "requirements",
    AgentType.PROJECT_CHARTER: "project_charter",
    AgentType.USER_STORIES: "user_stories",
    AgentType.BUSINESS_MODEL: "business_model",
    AgentType.MARKETING_PLAN: "marketing_plan",
    AgentType.PM_DOCUMENTATION: "pm_documentation",
    AgentType.STAKEHOLDER_COMMUNICATION: "stakeholder_communication",
    AgentType.WBS_AGENT: "wbs_agent",
    AgentType.TECHNICAL_DOCUMENTATION: "technical_documentation",
    AgentType.DATABASE_SCHEMA: "database_schema",
}


def get_output_filename_for_agent(agent_type: AgentType, filename: str) -> str:
    """
    Get the output filename with folder prefix based on agent type.
    
    Args:
        agent_type: AgentType enum value
        filename: Base filename (e.g., "requirements.md")
    
    Returns:
        Filename with folder prefix (e.g., "requirements/requirements.md")
    """
    folder = AGENT_TYPE_TO_FOLDER.get(agent_type)
    if folder:
        # Extract just the filename if path is provided
        filename_only = Path(filename).name
        return f"{folder}/{filename_only}"
    return filename


class WorkflowCoordinator:
    """
    Coordinates the multi-agent documentation generation workflow
    
    Workflow:
    1. Requirements Analyst → Requirements Doc
    2. PM Agent → Project Management Docs
    3. (Future: Technical, API, Developer, Stakeholder agents)
    """
    
    def __init__(
        self,
        context_manager: Optional[ContextManager] = None,
        rate_limiter: Optional[RequestQueue] = None,
        provider_name: Optional[str] = None,
        provider_config: Optional[Dict[str, str]] = None
    ):
        """
        Initialize workflow coordinator
        
        Args:
            context_manager: Context manager instance
            rate_limiter: Shared rate limiter for all agents
            provider_name: Default provider name for all agents (if None, uses LLM_PROVIDER env var or settings)
            provider_config: Optional dict mapping agent keys to provider names for per-agent configuration
                           Example: {"requirements_analyst": "gemini", "api_agent": "ollama"}
        """
        settings = get_settings()
        self.context_manager = context_manager or ContextManager()
        # Use rate limit from settings
        self.rate_limiter = rate_limiter or RequestQueue(
            max_rate=settings.rate_limit_per_minute, 
            period=60
        )
        self.file_manager = FileManager(base_dir=settings.docs_dir)
        logger.info(f"WorkflowCoordinator initialized (environment: {settings.environment.value})")
        
        # Determine default provider
        # Priority: provider_name parameter > LLM_PROVIDER env var > settings.default_llm_provider > "gemini"
        if provider_name is None:
            provider_name = os.getenv("LLM_PROVIDER") or settings.default_llm_provider or "gemini"
        provider_name = provider_name.lower()
        
        # Parse provider_config (per-agent configuration)
        provider_config = provider_config or {}
        self.provider_config = {k.lower(): v.lower() for k, v in provider_config.items()}
        self.default_provider = provider_name
        
        # Log provider configuration
        logger.info(f"🔧 Provider configuration:")
        logger.info(f"   Default provider: {self.default_provider}")
        if self.provider_config:
            logger.info(f"   Per-agent overrides: {len(self.provider_config)} agents")
            for agent_key, agent_provider in self.provider_config.items():
                logger.info(f"     - {agent_key}: {agent_provider}")
        else:
            logger.info(f"   All agents using default provider: {self.default_provider}")
        
        # Helper function to get provider for an agent
        def get_agent_provider(agent_key: str) -> str:
            """
            Get provider for a specific agent
            
            Priority:
            1. provider_config[agent_key] (per-agent override)
            2. default_provider (from parameter or env var)
            
            Args:
                agent_key: Agent identifier (e.g., "requirements_analyst")
            
            Returns:
                Provider name (e.g., "gemini", "ollama", "openai")
            """
            # Check for per-agent override
            if agent_key.lower() in self.provider_config:
                return self.provider_config[agent_key.lower()]
            # Use default provider
            return self.default_provider
        
        # Initialize agents (shared rate limiter, with optional provider override)
        self.requirements_analyst = RequirementsAnalyst(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("requirements_analyst")
        )
        self.pm_agent = PMDocumentationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("pm_agent")
        )
        self.technical_agent = TechnicalDocumentationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("technical_agent")
        )
        self.api_agent = APIDocumentationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("api_agent")
        )
        self.developer_agent = DeveloperDocumentationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("developer_agent")
        )
        self.stakeholder_agent = StakeholderCommunicationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("stakeholder_agent")
        )
        self.wbs_agent = WBSAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("wbs_agent")
        )
        self.user_agent = UserDocumentationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("user_agent")
        )
        self.test_agent = TestDocumentationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("test_agent")
        )
        self.quality_reviewer = QualityReviewerAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("quality_reviewer")
        )
        self.format_converter = FormatConverterAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("format_converter")
        )
        self.claude_cli_agent = ClaudeCLIDocumentationAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("claude_cli_agent")
        )
        self.cross_referencer = CrossReferencer()
        
        # Level 1: Strategic (Entrepreneur) - New agents
        self.project_charter_agent = ProjectCharterAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("project_charter_agent")
        )
        
        # Level 2: Product (Product Manager) - New agents
        self.user_stories_agent = UserStoriesAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("user_stories_agent")
        )
        
        # Level 3: Technical (Programmer) - New agents
        self.database_schema_agent = DatabaseSchemaAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("database_schema_agent")
        )
        self.setup_guide_agent = SetupGuideAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("setup_guide_agent")
        )
        
        # Business & Marketing agents
        self.marketing_plan_agent = MarketingPlanAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("marketing_plan_agent")
        )
        self.business_model_agent = BusinessModelAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("business_model_agent")
        )
        self.support_playbook_agent = SupportPlaybookAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("support_playbook_agent")
        )
        self.legal_compliance_agent = LegalComplianceAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("legal_compliance_agent")
        )
        
        # Document improvement agent (for auto-fix loop)
        self.document_improver = DocumentImproverAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("document_improver")
        )
        
        # Code Analyst Agent (for code-first workflow)
        self.code_analyst = CodeAnalystAgent(
            rate_limiter=self.rate_limiter,
            provider_name=get_agent_provider("code_analyst"),
            file_manager=self.file_manager
        )
        
        # Log final configuration summary
        used_providers = set([self.default_provider] + list(self.provider_config.values()))
        logger.info(f"✅ WorkflowCoordinator configured with {len(used_providers)} provider(s): {', '.join(sorted(used_providers))}")
        
        logger.info("WorkflowCoordinator initialized with all agents")
    
    def _run_agent_with_quality_loop(
        self,
        agent_instance,
        agent_type: AgentType,
        generate_kwargs: dict,
        output_filename: str,
        project_id: str,
        quality_threshold: float = 80.0
    ) -> tuple:
        """
        Runs an agent, checks its quality, and improves it if below the threshold.
        This implements the "Quality Gate" pattern for foundational documents.
        
        Args:
            agent_instance: Agent instance to run
            agent_type: AgentType enum value
            generate_kwargs: Keyword arguments to pass to agent.generate_and_save()
            output_filename: Output filename
            project_id: Project ID
            quality_threshold: Quality score threshold (default: 80.0)
        
        Returns:
            Tuple of (final_file_path, final_content)
        """
        logger.info(f"🔍 Running Quality Loop for {agent_type.value}...")
        
        # 1. GENERATE V1
        logger.info(f"  📝 Step 1: Generating V1 for {agent_type.value}...")
        try:
            # generate_kwargs should already contain output_filename, project_id, context_manager
            # Only pass them explicitly if not in generate_kwargs (for backward compatibility)
            call_kwargs = generate_kwargs.copy()
            if "output_filename" not in call_kwargs:
                call_kwargs["output_filename"] = output_filename
            if "project_id" not in call_kwargs:
                call_kwargs["project_id"] = project_id
            if "context_manager" not in call_kwargs:
                call_kwargs["context_manager"] = self.context_manager
            
            v1_file_path = agent_instance.generate_and_save(**call_kwargs)
            v1_content = self.file_manager.read_file(v1_file_path)
            logger.info(f"  ✅ V1 generated: {len(v1_content)} characters")
        except Exception as e:
            logger.error(f"  ❌ V1 generation failed for {agent_type.value}: {e}")
            raise
        
        # 2. CHECK V1 QUALITY
        logger.info(f"  🔍 Step 2: Checking V1 quality for {agent_type.value}...")
        score = 0
        quality_result_v1 = None  # Initialize to ensure it's in scope
        try:
            # Get checklist for this agent type
            checklist = self.quality_reviewer.document_type_checker.get_checklist_for_agent(agent_type)
            
            if checklist:
                # Use document-type-specific quality checker
                quality_result_v1 = self.quality_reviewer.document_type_checker.check_quality_for_type(
                    v1_content,
                    document_type=agent_type.value
                )
                score = quality_result_v1.get("overall_score", 0)
                logger.info(f"  📊 V1 Quality Score: {score:.2f}/100 (threshold: {quality_threshold})")
            else:
                logger.warning(f"  ⚠️  No quality checklist found for {agent_type.value}, using base checker")
                # Fallback to base checker
                quality_result_v1 = self.quality_reviewer.quality_checker.check_quality(v1_content)
                score = quality_result_v1.get("overall_score", 0)
                logger.info(f"  📊 V1 Quality Score: {score:.2f}/100 (threshold: {quality_threshold})")
        except Exception as e:
            logger.warning(f"  ⚠️  Quality check failed for {agent_type.value}: {e}, assuming score 0 to trigger improvement")
            score = 0
            quality_result_v1 = None
        
        # 3. DECIDE AND IMPROVE
        if score >= quality_threshold:
            logger.info(f"  ✅ [{agent_type.value}] V1 quality ({score:.2f}/100) meets threshold ({quality_threshold}). Proceeding.")
            return v1_file_path, v1_content
        else:
            logger.warning(f"  ⚠️  [{agent_type.value}] V1 quality ({score:.2f}/100) is below threshold ({quality_threshold}). Triggering improvement loop...")
            
            # 3a. Get Actionable Feedback
            logger.info(f"  🔍 Step 3a: Generating quality feedback for {agent_type.value}...")
            try:
                feedback_report = self.quality_reviewer.generate(
                    {agent_type.value: v1_content}
                )
                logger.info(f"  ✅ Quality feedback generated: {len(feedback_report)} characters")
            except Exception as e:
                logger.warning(f"  ⚠️  Quality feedback generation failed: {e}, using simplified feedback")
                # Create a simple feedback if generation fails
                feedback_report = f"""
Quality Review for {agent_type.value}:

Current Score: {score:.2f}/100
Threshold: {quality_threshold}

Issues Found:
- Document quality is below the required threshold
- Please improve completeness, clarity, and structure
- Ensure all required sections are present and well-developed

Improvement Suggestions:
- Review and expand missing sections
- Improve clarity and readability
- Add more detailed explanations
- Ensure technical accuracy
"""
            
            # 3b. Improve V1 -> V2
            logger.info(f"  🔧 Step 3b: Improving {agent_type.value} (V1 -> V2)...")
            try:
                # Pass quality score and details to improver for better context
                quality_score_for_improver = score
                quality_details_for_improver = None
                
                if quality_result_v1:
                    quality_details_for_improver = {
                        "word_count": quality_result_v1.get("word_count", {}),
                        "sections": quality_result_v1.get("sections", {}),
                        "readability": quality_result_v1.get("readability", {})
                    }
                
                # Use improved method with quality context
                improved_doc = self.document_improver.improve_document(
                    original_document=v1_content,
                    document_type=agent_type.value,
                    quality_feedback=feedback_report,
                    quality_score=quality_score_for_improver,
                    quality_details=quality_details_for_improver
                )
                
                # Save improved document
                v2_file_path = self.file_manager.write_file(output_filename, improved_doc)
                logger.info(f"Improved {agent_type.value} saved to: {v2_file_path}")
                
                # Save to context
                if self.context_manager:
                    try:
                        from src.context.shared_context import AgentOutput, DocumentStatus
                        from datetime import datetime
                        output = AgentOutput(
                            agent_type=agent_type,
                            document_type=agent_type.value,
                            content=improved_doc,
                            file_path=v2_file_path,
                            status=DocumentStatus.COMPLETE,
                            generated_at=datetime.now()
                        )
                        self.context_manager.save_agent_output(project_id, output)
                        logger.debug(f"Improved {agent_type.value} saved to context")
                    except Exception as e:
                        logger.warning(f"Could not save improved document to context: {e}")
                
                v2_content = improved_doc
                logger.info(f"  ✅ V2 (Improved) generated: {len(v2_content)} characters")
                
                # Optionally check V2 quality (for logging)
                try:
                    checklist = self.quality_reviewer.document_type_checker.get_checklist_for_agent(agent_type)
                    if checklist:
                        quality_result_v2 = self.quality_reviewer.document_type_checker.check_quality_for_type(
                            v2_content,
                            document_type=agent_type.value
                        )
                        v2_score = quality_result_v2.get("overall_score", 0)
                        logger.info(f"  📊 V2 Quality Score: {v2_score:.2f}/100 (improvement: +{v2_score - score:.2f})")
                except Exception as e:
                    logger.debug(f"  ⚠️  V2 quality check skipped: {e}")
                
                logger.info(f"  🎉 [{agent_type.value}] Quality loop completed: V1 ({score:.2f}) -> V2 (improved)")
                return v2_file_path, v2_content
            except Exception as e:
                logger.error(f"  ❌ Improvement failed for {agent_type.value}: {e}")
                # If improvement fails, return V1 as fallback
                logger.warning(f"  ⚠️  Falling back to V1 for {agent_type.value}")
                return v1_file_path, v1_content
    
    async def _async_run_agent_with_quality_loop(
        self,
        agent_instance,
        agent_type: AgentType,
        generate_kwargs: dict,
        output_filename: Optional[str] = None,
        project_id: Optional[str] = None,
        quality_threshold: float = 80.0
    ) -> tuple:
        """
        Runs an agent asynchronously, checks its quality, and improves it if below the threshold.
        Async version of _run_agent_with_quality_loop.
        
        Args:
            agent_instance: Agent instance to run
            agent_type: AgentType enum value
            generate_kwargs: Keyword arguments to pass to agent.generate_and_save()
                (should already contain output_filename, project_id, context_manager)
            output_filename: Output filename (optional, extracted from generate_kwargs if not provided)
            project_id: Project ID (optional, extracted from generate_kwargs if not provided)
            quality_threshold: Quality score threshold (default: 80.0)
        
        Returns:
            Tuple of (final_file_path, final_content)
        """
        logger.info(f"🔍 Running Quality Loop (async) for {agent_type.value}...")
        
        # Extract output_filename and project_id from generate_kwargs if not provided explicitly
        # generate_kwargs already contains these, so we extract them for later use
        if output_filename is None:
            output_filename = generate_kwargs.get("output_filename")
        if project_id is None:
            project_id = generate_kwargs.get("project_id")
        if project_id is None:
            raise ValueError("project_id must be provided either as parameter or in generate_kwargs")
        
        # 1. GENERATE V1 (async)
        logger.info(f"  📝 Step 1: Generating V1 (async) for {agent_type.value}...")
        try:
            # generate_kwargs already contains output_filename, project_id, context_manager
            # Don't pass them again to avoid "multiple values" error
            loop = asyncio.get_event_loop()
            v1_file_path = await loop.run_in_executor(
                None,
                lambda: agent_instance.generate_and_save(**generate_kwargs)
            )
            
            # Read file (can be async in future, but FileManager is sync for now)
            v1_content = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.file_manager.read_file(v1_file_path)
            )
            logger.info(f"  ✅ V1 generated (async): {len(v1_content)} characters")
        except Exception as e:
            logger.error(f"  ❌ V1 generation failed for {agent_type.value}: {e}")
            raise
        
        # 2. CHECK V1 QUALITY (async)
        logger.info(f"  🔍 Step 2: Checking V1 quality (async) for {agent_type.value}...")
        score = 0
        quality_result_v1 = None  # Initialize to ensure it's in scope
        try:
            loop = asyncio.get_event_loop()
            checklist = await loop.run_in_executor(
                None,
                lambda: self.quality_reviewer.document_type_checker.get_checklist_for_agent(agent_type)
            )
            
            if checklist:
                quality_result_v1 = await loop.run_in_executor(
                    None,
                    lambda: self.quality_reviewer.document_type_checker.check_quality_for_type(
                        v1_content,
                        document_type=agent_type.value
                    )
                )
                score = quality_result_v1.get("overall_score", 0)
                logger.info(f"  📊 V1 Quality Score (async): {score:.2f}/100 (threshold: {quality_threshold})")
            else:
                quality_result_v1 = await loop.run_in_executor(
                    None,
                    lambda: self.quality_reviewer.quality_checker.check_quality(v1_content)
                )
                score = quality_result_v1.get("overall_score", 0)
                logger.info(f"  📊 V1 Quality Score (async): {score:.2f}/100 (threshold: {quality_threshold})")
        except Exception as e:
            logger.warning(f"  ⚠️  Quality check failed for {agent_type.value}: {e}, assuming score 0")
            score = 0
            quality_result_v1 = None
        
        # Save V1 as version 1 to database
        if self.context_manager:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.context_manager.save_document_version(
                        project_id=project_id,
                        agent_type=agent_type,
                        content=v1_content,
                        file_path=v1_file_path,
                        quality_score=score,
                        version=1
                    )
                )
                logger.info(f"  💾 V1 saved as version 1 to database")
            except Exception as e:
                logger.warning(f"  ⚠️  Could not save V1 to database: {e}")
        
        # 3. DECIDE AND IMPROVE (async) - Iterative improvement loop
        current_version = 1
        current_content = v1_content
        current_file_path = v1_file_path
        current_score = score
        max_iterations = 3  # Maximum number of improvement iterations
        
        for iteration in range(1, max_iterations + 1):
            if current_score >= quality_threshold:
                logger.info(f"  ✅ [{agent_type.value}] Version {current_version} quality ({current_score:.2f}/100) meets threshold. Proceeding.")
                return current_file_path, current_content
            
            logger.warning(f"  ⚠️  [{agent_type.value}] Version {current_version} quality ({current_score:.2f}/100) is below threshold. Iteration {iteration}/{max_iterations}...")
            
            # 3a. Get Actionable Feedback (async)
            logger.info(f"  🔍 Step 3a: Generating quality feedback for iteration {iteration} (async)...")
            try:
                loop = asyncio.get_event_loop()
                feedback_report = await loop.run_in_executor(
                    None,
                    lambda: self.quality_reviewer.generate({agent_type.value: current_content})
                )
                logger.info(f"  ✅ Quality feedback generated (async): {len(feedback_report)} characters")
            except Exception as e:
                logger.warning(f"  ⚠️  Quality feedback generation failed: {e}, using simplified feedback")
                feedback_report = f"""
Quality Review for {agent_type.value} (Version {current_version}):

Current Score: {current_score:.2f}/100
Threshold: {quality_threshold}

Issues Found:
- Document quality is below the required threshold
- Please improve completeness, clarity, and structure
- Ensure all required sections are present and well-developed

Improvement Suggestions:
- Review and expand missing sections
- Improve clarity and readability
- Add more detailed explanations
- Ensure technical accuracy
"""
            
            # 3b. Incremental Improvement (async) - Only improve what's missing
            logger.info(f"  🔧 Step 3b: Incremental improvement iteration {iteration} (V{current_version} -> V{current_version + 1}, async)...")
            try:
                # Get quality details for incremental improvement
                quality_details_for_improver = None
                if quality_result_v1:
                    quality_details_for_improver = {
                        "word_count": quality_result_v1.get("word_count", {}),
                        "sections": quality_result_v1.get("sections", {}),
                        "readability": quality_result_v1.get("readability", {}),
                        "current_score": current_score,
                        "threshold": quality_threshold
                    }
                
                # Use incremental improvement method (async)
                # This should only add/improve missing parts, not rewrite everything
                loop = asyncio.get_event_loop()
                improved_doc = await loop.run_in_executor(
                    None,
                    lambda: self.document_improver.improve_document(
                        original_document=current_content,  # Use current version as base
                        document_type=agent_type.value,
                        quality_feedback=feedback_report,
                        quality_score=current_score,
                        quality_details=quality_details_for_improver,
                        focus_areas=["missing_sections", "incomplete_sections", "low_quality_sections"]  # Focus on what's missing
                    )
                )
                
                # Save improved document as new version (async)
                new_version = current_version + 1
                improved_file_path = await loop.run_in_executor(
                    None,
                    lambda: self.file_manager.write_file(output_filename, improved_doc)
                )
                logger.info(f"Incremental improvement V{new_version} saved (async) to: {improved_file_path}")
                
                # Save new version to database
                if self.context_manager:
                    try:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            None,
                            lambda: self.context_manager.save_document_version(
                                project_id=project_id,
                                agent_type=agent_type,
                                content=improved_doc,
                                file_path=improved_file_path,
                                quality_score=None,  # Will be checked next
                                version=new_version
                            )
                        )
                        logger.info(f"  💾 V{new_version} saved to database")
                    except Exception as e:
                        logger.warning(f"Could not save V{new_version} to database: {e}")
                
                # Check quality of improved version
                logger.info(f"  🔍 Checking quality of V{new_version}...")
                try:
                    checklist = await loop.run_in_executor(
                        None,
                        lambda: self.quality_reviewer.document_type_checker.get_checklist_for_agent(agent_type)
                    )
                    if checklist:
                        quality_result_new = await loop.run_in_executor(
                            None,
                            lambda: self.quality_reviewer.document_type_checker.check_quality_for_type(
                                improved_doc,
                                document_type=agent_type.value
                            )
                        )
                        new_score = quality_result_new.get("overall_score", 0)
                        improvement = new_score - current_score
                        logger.info(f"  📊 V{new_version} Quality Score (async): {new_score:.2f}/100 (improvement: +{improvement:.2f})")
                        
                        # Update for next iteration
                        current_version = new_version
                        current_content = improved_doc
                        current_file_path = improved_file_path
                        current_score = new_score
                        quality_result_v1 = quality_result_new  # Update for next iteration
                    else:
                        # Fallback quality check
                        quality_result_new = await loop.run_in_executor(
                            None,
                            lambda: self.quality_reviewer.quality_checker.check_quality(improved_doc)
                        )
                        new_score = quality_result_new.get("overall_score", 0)
                        improvement = new_score - current_score
                        logger.info(f"  📊 V{new_version} Quality Score (async): {new_score:.2f}/100 (improvement: +{improvement:.2f})")
                        
                        current_version = new_version
                        current_content = improved_doc
                        current_file_path = improved_file_path
                        current_score = new_score
                        quality_result_v1 = quality_result_new
                except Exception as e:
                    logger.warning(f"  ⚠️  Quality check for V{new_version} failed: {e}, assuming improvement")
                    # Still update to new version even if quality check fails
                    current_version = new_version
                    current_content = improved_doc
                    current_file_path = improved_file_path
                
                logger.info(f"  ✅ Iteration {iteration} completed: V{current_version} (score: {current_score:.2f})")
                
            except Exception as e:
                logger.error(f"  ❌ Improvement iteration {iteration} failed for {agent_type.value}: {e}")
                if iteration == 1:
                    logger.warning(f"  ⚠️  Falling back to V1 for {agent_type.value}")
                    return v1_file_path, v1_content
                else:
                    # Return the best version we have so far
                    logger.warning(f"  ⚠️  Returning best version so far (V{current_version})")
                    break
        
        # Return the best version we achieved
        logger.info(f"  🎉 [{agent_type.value}] Quality loop completed: Final version V{current_version} (score: {current_score:.2f})")
        return current_file_path, current_content
    
    def _generate_technical_doc(self, req_summary, project_id):
        """Helper for parallel technical doc generation"""
        return self.technical_agent.generate_and_save(
            requirements_summary=req_summary,
            output_filename=get_output_filename_for_agent(AgentType.TECHNICAL_DOCUMENTATION, "technical_spec.md"),
            project_id=project_id,
            context_manager=self.context_manager
        )
    
    def _generate_stakeholder_doc(self, req_summary, pm_path, project_id):
        """Helper for parallel stakeholder doc generation"""
        pm_summary = self._get_summary_from_file(pm_path)
        return self.stakeholder_agent.generate_and_save(
            requirements_summary=req_summary,
            pm_summary=pm_summary,
            output_filename="stakeholder_summary.md",
            project_id=project_id,
            context_manager=self.context_manager
        )
    
    def _generate_user_doc(self, req_summary, project_id):
        """Helper for parallel user doc generation"""
        return self.user_agent.generate_and_save(
            requirements_summary=req_summary,
            output_filename="user_guide.md",
            project_id=project_id,
            context_manager=self.context_manager
        )
    
    def generate_all_docs(
        self,
        user_idea: str,
        project_id: Optional[str] = None,
        profile: str = "team",
        codebase_path: Optional[str] = None,
        workflow_mode: str = "docs_first"
    ) -> Dict:
        """
        Generate all documentation types from a user idea using HYBRID workflow:
        - Phase 0 (Code-First mode): Code analysis (optional, if codebase_path provided and workflow_mode="code_first")
        - Phase 1: Foundational documents with Quality Gate (iterative improvement)
        - Phase 2: Secondary documents in parallel (fast execution)
        - Phase 3: Final packaging (cross-ref, review, convert)
        - Phase 4: Code analysis and documentation update (optional, if codebase_path provided and workflow_mode="docs_first")
        
        Args:
            user_idea: User's project idea
            project_id: Optional project ID (generates one if not provided)
            profile: "team" or "individual" - determines which docs to generate
            codebase_path: Optional path to codebase directory.
                         - If workflow_mode="code_first": Code analysis runs BEFORE Phase 1, results are used as input for Technical and API docs
                         - If workflow_mode="docs_first": Code analysis runs in Phase 4, updates existing docs to match actual code
            workflow_mode: "docs_first" (default) or "code_first"
                          - "docs_first": Generate docs first, then update with code analysis (Phase 4)
                          - "code_first": Analyze code first, then generate docs based on actual code (Phase 0)
        
        Returns:
            Dict with generated file paths and status
        """
        # --- SETUP ---
        if not project_id:
            project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        workflow_mode = workflow_mode.lower()
        if workflow_mode not in ["docs_first", "code_first"]:
            logger.warning(f"Invalid workflow_mode '{workflow_mode}', using 'docs_first'")
            workflow_mode = "docs_first"
        
        logger.info(f"🚀 Starting HYBRID Workflow - Project ID: {project_id}, Profile: {profile}, Mode: {workflow_mode}")
        
        results = {
            "project_id": project_id,
            "user_idea": user_idea,
            "profile": profile,
            "workflow_mode": workflow_mode,
            "files": {},
            "status": {}
        }
        
        # Store final, high-quality document content
        final_docs = {}
        document_file_paths = {}
        
        # Store code analysis results (for code-first mode)
        code_analysis_result = None
        code_analysis_summary = None
        
        try:
            # --- PHASE 0: CODE ANALYSIS (Code-First Mode) ---
            if workflow_mode == "code_first" and codebase_path:
                logger.info("=" * 80)
                logger.info("--- PHASE 0: Code Analysis (Code-First Mode) ---")
                logger.info("=" * 80)
                logger.info(f"📁 Analyzing codebase at: {codebase_path}")
                
                try:
                    # Analyze codebase
                    logger.info("🔍 Analyzing codebase structure...")
                    code_analysis_result = self.code_analyst.analyze_codebase(codebase_path)
                    logger.info(f"  ✅ Code analysis complete: {len(code_analysis_result.get('modules', []))} modules, "
                              f"{len(code_analysis_result.get('classes', []))} classes, "
                              f"{len(code_analysis_result.get('functions', []))} functions")
                    
                    # Generate code analysis summary for use in documentation
                    code_analysis_summary = f"""
# Codebase Analysis Summary

## Modules Analyzed: {len(code_analysis_result.get('modules', []))}
## Classes Found: {len(code_analysis_result.get('classes', []))}
## Functions Found: {len(code_analysis_result.get('functions', []))}

## Key Classes:
"""
                    for cls in code_analysis_result.get('classes', [])[:20]:  # Limit to first 20
                        code_analysis_summary += f"""
### {cls.get('name', 'Unknown')} (in {cls.get('file', 'unknown')})
- Docstring: {cls.get('docstring', 'No docstring')}
- Methods: {len(cls.get('methods', []))}
- Bases: {', '.join(cls.get('bases', []))}
"""
                    
                    code_analysis_summary += "\n## Key Functions:\n"
                    for func in code_analysis_result.get('functions', [])[:20]:  # Limit to first 20
                        code_analysis_summary += f"""
### {func.get('name', 'Unknown')} (in {func.get('file', 'unknown')})
- Docstring: {func.get('docstring', 'No docstring')}
- Args: {', '.join(func.get('args', []))}
"""
                    
                    # Store code analysis in context for use in Phase 1 and Phase 2
                    # We'll pass this to agents via kwargs
                    logger.info("  ✅ Code analysis summary generated for use in documentation generation")
                    results["status"]["code_analysis"] = "complete"
                    results["code_analysis"] = {
                        "modules_count": len(code_analysis_result.get('modules', [])),
                        "classes_count": len(code_analysis_result.get('classes', [])),
                        "functions_count": len(code_analysis_result.get('functions', []))
                    }
                    
                except Exception as e:
                    logger.error(f"  ❌ Phase 0 (Code Analysis) failed: {e}", exc_info=True)
                    results["status"]["code_analysis"] = "failed"
                    results["code_analysis_error"] = str(e)
                    # Continue with docs-first mode if code analysis fails
                    logger.warning("  ⚠️  Continuing with docs-first mode (code analysis failed)")
                    workflow_mode = "docs_first"
                    code_analysis_result = None
                    code_analysis_summary = None
            
            # --- PHASE 1: FOUNDATIONAL DOCUMENTS (DAG with Quality Gate) ---
            logger.info("=" * 80)
            logger.info("--- PHASE 1: Generating Foundational Documents (DAG with Quality Gate) ---")
            logger.info("=" * 80)
            
            # Get Phase 1 task configurations from DAG
            phase1_tasks = get_phase1_tasks_for_profile(profile=profile)
            logger.info(f"📋 Phase 1 DAG: {len(phase1_tasks)} tasks for profile '{profile}'")
            
            # Build dependency map
            phase1_dependency_map = build_phase1_task_dependencies(phase1_tasks)
            
            # Create async executor for Phase 1
            executor = AsyncParallelExecutor(max_workers=4)  # Smaller pool for Phase 1
            
            # Create async task execution coroutines for each Phase 1 task
            def create_phase1_task_coro(task: Phase1Task):
                """Create an async task coroutine that executes Phase 1 task with quality gate"""
                async def execute_phase1_task():
                    # Get dependencies from context (AsyncParallelExecutor ensures dependencies are completed first)
                    deps_content: Dict[AgentType, str] = {}
                    loop = asyncio.get_event_loop()
                    
                    for dep_type in task.dependencies:
                        dep_type_capture = dep_type
                        dep_output = await loop.run_in_executor(
                            None,
                            lambda dt=dep_type_capture: self.context_manager.get_agent_output(project_id, dt)
                        )
                        if dep_output:
                            deps_content[dep_type] = dep_output.content
                        else:
                            # Optional dependencies (like PROJECT_CHARTER for individual profile) may be None
                            logger.debug(f"  ℹ️  Phase 1 dependency {dep_type.value} not found in context for {task.task_id} (may be optional)")
                            deps_content[dep_type] = None
                    
                    # Build kwargs for agent.generate_and_save
                    # Pass code_analysis_summary if available (code-first mode)
                    kwargs = build_kwargs_for_phase1_task(
                        task=task,
                        user_idea=user_idea,
                        project_id=project_id,
                        context_manager=self.context_manager,
                        deps_content=deps_content,
                        code_analysis_summary=code_analysis_summary  # Pass code analysis for code-first mode
                    )
                    
                    # Note: Each Phase 1 agent has its own FileManager with base_dir set to docs/{folder}
                    # For example: RequirementsAnalyst has base_dir="docs/requirements"
                    # So we just need to pass the filename (e.g., "requirements.md"), NOT the folder prefix
                    # The folder prefix would cause duplicate paths like docs/requirements/requirements/requirements.md
                    # build_kwargs_for_phase1_task already returns the correct filename from task.output_filename
                    # So we don't need to call get_output_filename_for_agent here
                    
                    # Get agent instance
                    agent = get_agent_for_phase1_task(self, task.agent_type)
                    if not agent:
                        raise ValueError(f"Agent not found for {task.agent_type.value}")
                    
                    # Execute with quality gate (async version)
                    logger.info(f"🔍 Executing Phase 1 task {task.task_id} with quality gate (threshold: {task.quality_threshold})...")
                    # kwargs already contains output_filename, project_id, context_manager
                    # Pass None for output_filename and project_id so they're extracted from kwargs
                    file_path, content = await self._async_run_agent_with_quality_loop(
                        agent_instance=agent,
                        agent_type=task.agent_type,
                        generate_kwargs=kwargs,
                        output_filename=None,  # Will be extracted from kwargs
                        project_id=None,  # Will be extracted from kwargs
                        quality_threshold=task.quality_threshold
                    )
                    
                    # Result is automatically saved to context by _async_run_agent_with_quality_loop
                    # Just return the result, it will be collected by AsyncParallelExecutor
                    logger.info(f"✅ Phase 1 task {task.task_id} completed: {len(content)} characters")
                    return file_path, content
                
                return execute_phase1_task
            
            # Add all Phase 1 tasks to async executor
            for task in phase1_tasks:
                task_coro = create_phase1_task_coro(task)()
                dep_task_ids = phase1_dependency_map.get(task.task_id, [])
                
                executor.add_task(
                    task_id=task.task_id,
                    coro=task_coro,
                    dependencies=dep_task_ids
                )
                logger.debug(f"  📝 Added Phase 1 async task: {task.task_id} (depends on: {dep_task_ids}, quality_threshold: {task.quality_threshold})")
            
            # Execute Phase 1 tasks asynchronously with dependency resolution
            logger.info("🚀 Executing Phase 1 tasks in parallel (respecting dependencies)...")
            # Run async executor in event loop (handle both sync and async contexts)
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                # If we're in an async context, we need to use a different approach
                # Create a new event loop in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor_pool:
                    future = executor_pool.submit(asyncio.run, executor.execute())
                    phase1_task_results = future.result()
            except RuntimeError:
                # No event loop running, we can use asyncio.run()
                phase1_task_results = asyncio.run(executor.execute())
            
            # Process Phase 1 results and update results dictionary
            req_content = None
            charter_content = None
            stories_content = None
            tech_content = None
            db_content = None
            
            for task in phase1_tasks:
                task_result = phase1_task_results.get(task.task_id)
                if task_result:
                    if isinstance(task_result, tuple) and len(task_result) == 2:
                        file_path, content = task_result
                    else:
                        # Handle case where result might be different format
                        logger.warning(f"Unexpected result format for {task.task_id}: {type(task_result)}")
                        continue
                    
                    # Map agent_type to doc_type for results storage
                    doc_type = AGENT_TYPE_TO_DOC_TYPE_PHASE1.get(task.agent_type, task.agent_type.value)
                    
                    # Update results dictionary
                    results["files"][doc_type] = file_path
                    results["status"][doc_type] = "complete_v2"
                    
                    # Store content for later use
                    final_docs[task.agent_type] = content
                    document_file_paths[task.agent_type] = file_path
                    
                    # Keep track of specific documents for validation
                    if task.agent_type == AgentType.REQUIREMENTS_ANALYST:
                        req_content = content
                    elif task.agent_type == AgentType.PROJECT_CHARTER:
                        charter_content = content
                    elif task.agent_type == AgentType.USER_STORIES:
                        stories_content = content
                    elif task.agent_type == AgentType.TECHNICAL_DOCUMENTATION:
                        tech_content = content
                    elif task.agent_type == AgentType.DATABASE_SCHEMA:
                        db_content = content
                else:
                    logger.error(f"❌ Phase 1 task {task.task_id} failed or returned no result")
                    # Mark as failed in status
                    doc_type = AGENT_TYPE_TO_DOC_TYPE_PHASE1.get(task.agent_type, task.agent_type.value)
                    results["status"][doc_type] = "failed"
            
            # Verify requirements were generated
            if not req_content:
                raise ValueError("Requirements not generated in Phase 1")
            
            # Get requirements summary from context
            context = self.context_manager.get_shared_context(project_id)
            if not context.requirements:
                raise ValueError("Requirements not found in context after generation")
            
            req_summary = context.get_requirements_summary()
            
            logger.info("=" * 80)
            logger.info("✅ PHASE 1 COMPLETE: Foundational documents generated with quality gates (DAG)")
            logger.info("=" * 80)
            
            # Get technical summary and database schema for Phase 2
            technical_summary = tech_content
            database_schema_summary = db_content
            
            # --- PHASE 2: PARALLEL GENERATION (DAG-based) ---
            logger.info("=" * 80)
            logger.info("--- PHASE 2: Generating Secondary Documents (Parallel DAG) ---")
            logger.info("=" * 80)
            
            # Get Phase 2 task configurations from DAG
            phase2_tasks = get_phase2_tasks_for_profile(profile=profile)
            logger.info(f"📋 Phase 2 DAG: {len(phase2_tasks)} tasks for profile '{profile}'")
            
            # Build dependency map (AgentType -> task_id dependencies)
            dependency_map = build_task_dependencies(phase2_tasks)
            
            # Prepare Phase 1 content for dependency extraction
            # Phase 1 documents are already complete, so we can use their content directly
            phase1_deps_content = {
                AgentType.REQUIREMENTS_ANALYST: req_content,
                AgentType.TECHNICAL_DOCUMENTATION: technical_summary,
                AgentType.DATABASE_SCHEMA: database_schema_summary,
                AgentType.PROJECT_CHARTER: charter_content if charter_content else None,
                AgentType.USER_STORIES: stories_content,
            }
            
            # Create async executor for Phase 2
            # Use AsyncParallelExecutor for true async parallel execution
            executor = AsyncParallelExecutor(max_workers=8)
            
            # Create async task execution coroutines for each Phase 2 task
            # These coroutines will extract dependencies from context when executed
            def create_async_task_coro(task: Phase2Task):
                """Create an async task coroutine that extracts dependencies and executes agent"""
                async def execute_async_task():
                    # Extract dependency content from context (for Phase 2 dependencies)
                    # Phase 1 dependencies are already available in phase1_deps_content
                    deps_content = phase1_deps_content.copy()
                    
                    # Get Phase 2 dependencies from context (these are completed in Phase 2)
                    # Note: We run sync context_manager calls in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    for dep_type in task.dependencies:
                        if dep_type not in deps_content:
                            # This is a Phase 2 dependency, fetch from context (async-safe)
                            # Capture dep_type in closure to avoid lambda issues
                            dep_type_capture = dep_type
                            dep_output = await loop.run_in_executor(
                                None,
                                lambda dt=dep_type_capture: self.context_manager.get_agent_output(project_id, dt)
                            )
                            if dep_output:
                                deps_content[dep_type] = dep_output.content
                            else:
                                # Dependency not yet available (shouldn't happen if dependencies are correct)
                                logger.warning(f"  ⚠️  Dependency {dep_type.value} not found in context for {task.task_id}")
                                deps_content[dep_type] = None
                    
                    # Build kwargs for agent.generate_and_save (sync function, but fast)
                    # Pass code_analysis_summary if available (code-first mode)
                    kwargs = build_kwargs_for_task(
                        task=task,
                        coordinator=self,
                        req_summary=req_summary,
                        technical_summary=technical_summary,
                        charter_content=charter_content,
                        project_id=project_id,
                        context_manager=self.context_manager,
                        deps_content=deps_content,
                        code_analysis_summary=code_analysis_summary  # Pass code analysis for code-first mode
                    )
                    
                    # Apply folder prefix to output_filename based on agent type
                    if "output_filename" in kwargs:
                        kwargs["output_filename"] = get_output_filename_for_agent(task.agent_type, kwargs["output_filename"])
                    
                    # Get agent instance
                    agent = get_agent_for_task(self, task.agent_type)
                    if not agent:
                        raise ValueError(f"Agent not found for {task.agent_type.value}")
                    
                    # Execute agent.generate_and_save (async if available, otherwise sync in executor)
                    # Check if agent has async_generate_and_save method first
                    if hasattr(agent, 'async_generate_and_save') and asyncio.iscoroutinefunction(agent.async_generate_and_save):
                        # Native async method (best performance)
                        result = await agent.async_generate_and_save(**kwargs)
                    elif hasattr(agent, 'generate_and_save') and asyncio.iscoroutinefunction(agent.generate_and_save):
                        # Async generate_and_save method
                        result = await agent.generate_and_save(**kwargs)
                    else:
                        # Fallback: run sync method in executor
                        result = await loop.run_in_executor(
                            None,
                            lambda kw=kwargs: agent.generate_and_save(**kw)
                        )
                    return result
                
                return execute_async_task
            
            # Add all tasks to async executor
            for task in phase2_tasks:
                # Create the async coroutine for this task
                task_coro = create_async_task_coro(task)()
                dep_task_ids = dependency_map.get(task.task_id, [])
                
                executor.add_task(
                    task_id=task.task_id,
                    coro=task_coro,
                    dependencies=dep_task_ids
                )
                logger.debug(f"  📝 Added async task: {task.task_id} (depends on: {dep_task_ids})")
            
            # Execute parallel tasks asynchronously
            # Note: Since generate_all_docs is sync, we need to run the async executor
            # We use asyncio.run() which creates a new event loop and runs until complete
            logger.info(f"🚀 Executing {len(executor.tasks)} parallel async tasks with DAG dependencies...")
            try:
                # Check if we're in an async context
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, but generate_all_docs is sync
                    # This shouldn't happen, but if it does, we'll use a thread
                    logger.warning("  ⚠️  generate_all_docs is sync but called from async context, using thread pool")
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor_pool:
                        future = executor_pool.submit(asyncio.run, executor.execute())
                        parallel_results = future.result()
                except RuntimeError:
                    # No event loop is running, we can use asyncio.run()
                    parallel_results = asyncio.run(executor.execute())
            except Exception as e:
                logger.error(f"  ❌ Error executing async tasks: {e}", exc_info=True)
                # Fallback to sync execution if async fails
                logger.warning("  ⚠️  Falling back to sync ParallelExecutor")
                from src.utils.parallel_executor import ParallelExecutor as SyncParallelExecutor
                sync_executor = SyncParallelExecutor(max_workers=8)
                
                # Re-add tasks to sync executor
                def create_sync_task_executor(task: Phase2Task):
                    def execute_task():
                        deps_content = phase1_deps_content.copy()
                        for dep_type in task.dependencies:
                            if dep_type not in deps_content:
                                dep_output = self.context_manager.get_agent_output(project_id, dep_type)
                                if dep_output:
                                    deps_content[dep_type] = dep_output.content
                                else:
                                    logger.warning(f"  ⚠️  Dependency {dep_type.value} not found in context for {task.task_id}")
                                    deps_content[dep_type] = None
                        kwargs = build_kwargs_for_task(
                            task=task,
                            coordinator=self,
                            req_summary=req_summary,
                            technical_summary=technical_summary,
                            charter_content=charter_content,
                            project_id=project_id,
                            context_manager=self.context_manager,
                            deps_content=deps_content
                        )
                        
                        # Apply folder prefix to output_filename based on agent type
                        if "output_filename" in kwargs:
                            kwargs["output_filename"] = get_output_filename_for_agent(task.agent_type, kwargs["output_filename"])
                        
                        agent = get_agent_for_task(self, task.agent_type)
                        if not agent:
                            raise ValueError(f"Agent not found for {task.agent_type.value}")
                        return agent.generate_and_save(**kwargs)
                    return execute_task
                
                for task in phase2_tasks:
                    task_executor = create_sync_task_executor(task)
                    dep_task_ids = dependency_map.get(task.task_id, [])
                    sync_executor.add_task(
                        task_id=task.task_id,
                        func=task_executor,
                        args=(),
                        dependencies=dep_task_ids
                    )
                parallel_results = sync_executor.execute()
            
            # Map AgentType to document type name for results
            # This mapping ensures consistency with the original implementation
            agent_type_to_doc_type = {
                AgentType.API_DOCUMENTATION: "api_documentation",
                AgentType.DATABASE_SCHEMA: "database_schema",
                AgentType.SETUP_GUIDE: "setup_guide",
                AgentType.DEVELOPER_DOCUMENTATION: "developer_documentation",
                AgentType.TEST_DOCUMENTATION: "test_documentation",
                AgentType.USER_DOCUMENTATION: "user_documentation",
                AgentType.LEGAL_COMPLIANCE: "legal_compliance",
                AgentType.SUPPORT_PLAYBOOK: "support_playbook",
                AgentType.PM_DOCUMENTATION: "pm_documentation",
                AgentType.STAKEHOLDER_COMMUNICATION: "stakeholder_documentation",
                AgentType.BUSINESS_MODEL: "business_model",
                AgentType.MARKETING_PLAN: "marketing_plan",
            }
            
            def get_doc_type_from_agent_type(agent_type: AgentType) -> str:
                """Convert AgentType to document type name for results"""
                return agent_type_to_doc_type.get(agent_type, agent_type.value)
            
            # Collect parallel task results with resilient error handling
            successful_tasks = []
            failed_tasks = []
            
            for task in phase2_tasks:
                task_id = task.task_id
                file_path = parallel_results.get(task_id)
                agent_type = task.agent_type
                doc_type = get_doc_type_from_agent_type(agent_type)
                
                # Check task status from executor
                task_status = executor.tasks.get(task_id)
                if task_status and task_status.status == TaskStatus.FAILED:
                    # Task failed - record error but continue processing other tasks
                    error = task_status.error if task_status.error else "Unknown error"
                    error_msg = str(error) if error else "Unknown error"
                    logger.error(f"  ❌ Task {task_id} ({doc_type}) failed: {error_msg}")
                    results["status"][doc_type] = "failed"
                    failed_tasks.append({
                        "task_id": task_id,
                        "doc_type": doc_type,
                        "agent_type": agent_type.value,
                        "error": error_msg
                    })
                elif file_path and task_status and task_status.status == TaskStatus.COMPLETE:
                    # Task succeeded
                    results["files"][doc_type] = file_path
                    results["status"][doc_type] = "complete"
                    
                    # Read content and add to final_docs
                    try:
                        content = self.file_manager.read_file(file_path)
                        final_docs[agent_type] = content
                        document_file_paths[agent_type] = file_path
                        logger.info(f"  ✅ {doc_type}: {file_path}")
                        successful_tasks.append({
                            "task_id": task_id,
                            "doc_type": doc_type,
                            "agent_type": agent_type.value,
                            "file_path": file_path
                        })
                    except Exception as e:
                        logger.warning(f"  ⚠️  Could not read {doc_type}: {e}")
                        # Mark as failed if we can't read the file
                        results["status"][doc_type] = "failed"
                        failed_tasks.append({
                            "task_id": task_id,
                            "doc_type": doc_type,
                            "agent_type": agent_type.value,
                            "error": f"Failed to read file: {str(e)}"
                        })
                else:
                    # Task status unknown or incomplete
                    logger.warning(f"  ⚠️  Task {task_id} ({doc_type}) has unknown status")
                    results["status"][doc_type] = "unknown"
                    failed_tasks.append({
                        "task_id": task_id,
                        "doc_type": doc_type,
                        "agent_type": agent_type.value,
                        "error": "Task status unknown or incomplete"
                    })
            
            # Log Phase 2 summary with success/failure breakdown
            logger.info("=" * 80)
            logger.info(f"✅ PHASE 2 COMPLETE: {len(successful_tasks)}/{len(phase2_tasks)} documents generated successfully")
            if successful_tasks:
                logger.info(f"   ✅ Successful: {', '.join([t['doc_type'] for t in successful_tasks])}")
            if failed_tasks:
                logger.warning(f"   ❌ Failed: {', '.join([t['doc_type'] for t in failed_tasks])}")
                for failed_task in failed_tasks:
                    logger.warning(f"      - {failed_task['doc_type']}: {failed_task['error']}")
            logger.info("=" * 80)
            
            # Store task execution summary in results for Phase 3 reporting
            results["phase2_summary"] = {
                "successful": successful_tasks,
                "failed": failed_tasks,
                "total": len(phase2_tasks),
                "success_count": len(successful_tasks),
                "failed_count": len(failed_tasks)
            }
            
            # --- PHASE 3: FINAL PACKAGING (Cross-ref, Review, Convert) ---
            logger.info("=" * 80)
            logger.info("--- PHASE 3: Final Packaging and Conversion ---")
            logger.info("=" * 80)
            
            # 1. Cross-Referencing
            logger.info("📎 Step 1: Adding cross-references to all documents...")
            try:
                referenced_docs = self.cross_referencer.create_cross_references(
                    final_docs,
                    document_file_paths
                )
                
                # Save cross-referenced documents back to files
                updated_count = 0
                for agent_type, referenced_content in referenced_docs.items():
                    original_content = final_docs.get(agent_type)
                    if referenced_content != original_content:
                        original_file_path = document_file_paths[agent_type]
                        # Write directly to original absolute path to preserve folder structure
                        if Path(original_file_path).is_absolute():
                            Path(original_file_path).write_text(referenced_content, encoding='utf-8')
                            logger.debug(f"Updated cross-referenced file: {original_file_path}")
                        else:
                            self.file_manager.write_file(original_file_path, referenced_content)
                        # Update final_docs for quality review
                        final_docs[agent_type] = referenced_content
                        updated_count += 1
                
                logger.info(f"  ✅ Added cross-references to {updated_count} documents")
                
                # Generate document index
                try:
                    index_content = self.cross_referencer.generate_document_index(
                        final_docs,
                        document_file_paths,
                        project_name=req_summary.get('project_overview', 'Project')[:50]
                    )
                    index_path = self.file_manager.write_file("index.md", index_content)
                    results["files"]["document_index"] = index_path
                    logger.info(f"  ✅ Document index created: {index_path}")
                except Exception as e:
                    logger.warning(f"  ⚠️  Could not generate index: {e}")
            except Exception as e:
                logger.warning(f"  ⚠️  Cross-referencing failed: {e}")
            
            # 2. Final Quality Review (generate report only)
            # Note: In hybrid mode, Phase 1 documents already went through quality gates
            # This review is for overall assessment and secondary documents
            logger.info("📊 Step 2: Generating final quality review report...")
            try:
                # Convert final_docs to dict with string keys for quality reviewer
                all_documentation_for_review = {
                    agent_type.value: content
                    for agent_type, content in final_docs.items()
                }
                
                quality_review_path = self.quality_reviewer.generate_and_save(
                    all_documentation=all_documentation_for_review,
                    output_filename="quality_review.md",
                    project_id=project_id,
                    context_manager=self.context_manager
                )
                results["files"]["quality_review"] = quality_review_path
                results["status"]["quality_review"] = "complete"
                logger.info(f"  ✅ Quality review report generated: {quality_review_path}")
            except Exception as e:
                logger.warning(f"  ⚠️  Quality review failed: {e}")
                results["status"]["quality_review"] = "failed"
            
            # 3. Claude CLI Documentation
            logger.info("📝 Step 3: Generating Claude CLI documentation...")
            try:
                claude_md_path = self.claude_cli_agent.generate_and_save(
                    all_documentation=final_docs,
                    project_id=project_id,
                    context_manager=self.context_manager
                )
                results["files"]["claude_cli_documentation"] = claude_md_path
                results["status"]["claude_cli_documentation"] = "complete"
                logger.info(f"  ✅ Claude CLI documentation generated: {claude_md_path}")
            except Exception as e:
                logger.warning(f"  ⚠️  Claude CLI documentation generation failed: {e}")
                results["status"]["claude_cli_documentation"] = "failed"
            
            # 4. Format Conversion
            logger.info("📄 Step 4: Converting documents to multiple formats...")
            try:
                # Prepare documents dict with proper names for format converter
                documents_for_conversion = {
                    agent_type.value: content
                    for agent_type, content in final_docs.items()
                }
                
                format_results = self.format_converter.convert_all_documents(
                    documents=documents_for_conversion,
                    formats=["html", "pdf", "docx"],
                    project_id=project_id,
                    context_manager=self.context_manager
                )
                results["files"]["format_conversions"] = format_results
                
                # Analyze conversion results to determine overall status
                total_docs = len(format_results)
                successful_formats = {}
                failed_formats = {}
                
                for doc_name, doc_results in format_results.items():
                    for fmt, fmt_result in doc_results.items():
                        if isinstance(fmt_result, dict) and fmt_result.get("status") == "success":
                            successful_formats[fmt] = successful_formats.get(fmt, 0) + 1
                        else:
                            failed_formats[fmt] = failed_formats.get(fmt, 0) + 1
                
                # Count successful conversions
                total_successful = sum(successful_formats.values())
                total_attempted = total_docs * 3  # 3 formats per document
                
                if total_successful == total_attempted:
                    results["status"]["format_conversions"] = "complete"
                    logger.info(f"  ✅ Converted {total_docs} documents to {total_successful} files (HTML, PDF, DOCX)")
                elif total_successful > 0:
                    results["status"]["format_conversions"] = f"partial ({total_successful}/{total_attempted} successful)"
                    logger.info(f"  ⚠️  Format conversion partial: {total_successful}/{total_attempted} successful")
                    # Log failed formats for debugging
                    for fmt, count in failed_formats.items():
                        logger.warning(f"    - {fmt.upper()}: {count} failures")
                else:
                    results["status"]["format_conversions"] = "failed"
                    logger.warning(f"  ❌ Format conversion failed: all {total_attempted} conversions failed")
                
                # Store conversion status details for frontend
                results["format_conversion_status"] = {
                    "successful": successful_formats,
                    "failed": failed_formats,
                    "total_docs": total_docs,
                    "total_successful": total_successful,
                    "total_attempted": total_attempted
                }
                
            except Exception as e:
                logger.error(f"  ❌ Format conversion failed with exception: {e}", exc_info=True)
                results["status"]["format_conversions"] = "failed"
                results["format_conversion_status"] = {
                    "error": str(e),
                    "successful": {},
                    "failed": {},
                    "total_docs": 0,
                    "total_successful": 0,
                    "total_attempted": 0
                }
            
            logger.info("=" * 80)
            logger.info("✅ PHASE 3 COMPLETE: Final packaging and conversion completed")
            logger.info("=" * 80)
            
            # Generate final execution summary report
            logger.info("=" * 80)
            logger.info("📊 FINAL EXECUTION SUMMARY")
            logger.info("=" * 80)
            
            # Count successful and failed documents across all phases
            all_successful_docs = []
            all_failed_docs = []
            
            # Phase 1 documents (from results["status"])
            # NOTE: technical_documentation and database_schema have been moved to Phase 2 for parallel execution
            # NOTE: business_model and marketing_plan have been moved to Phase 1 for quick decision-making
            phase1_doc_types = ["requirements", "project_charter", "user_stories", "business_model", "marketing_plan"]
            for doc_type in phase1_doc_types:
                if doc_type in results.get("status", {}):
                    if results["status"][doc_type] == "complete" or results["status"][doc_type] == "complete_v2":
                        all_successful_docs.append(doc_type)
                    elif results["status"][doc_type] == "failed":
                        all_failed_docs.append(doc_type)
            
            # Phase 2 documents (from phase2_summary)
            if "phase2_summary" in results:
                phase2_summary = results["phase2_summary"]
                for task in phase2_summary.get("successful", []):
                    all_successful_docs.append(task["doc_type"])
                for task in phase2_summary.get("failed", []):
                    all_failed_docs.append(task["doc_type"])
            
            # Phase 3 documents (quality_review, claude_cli_documentation, format_conversions, document_index)
            phase3_doc_types = ["quality_review", "claude_cli_documentation", "format_conversions", "document_index"]
            for doc_type in phase3_doc_types:
                if doc_type in results.get("status", {}):
                    status = results["status"][doc_type]
                    if status == "complete" or "partial" in status.lower():
                        all_successful_docs.append(doc_type)
                    elif status == "failed" or status == "skipped":
                        all_failed_docs.append(doc_type)
            
            # Log summary
            total_docs = len(all_successful_docs) + len(all_failed_docs)
            success_count = len(all_successful_docs)
            failed_count = len(all_failed_docs)
            
            logger.info(f"📈 Total Documents: {total_docs}")
            logger.info(f"✅ Successful: {success_count} ({success_count/total_docs*100:.1f}%)" if total_docs > 0 else "✅ Successful: 0")
            logger.info(f"❌ Failed: {failed_count} ({failed_count/total_docs*100:.1f}%)" if total_docs > 0 else "❌ Failed: 0")
            
            if all_successful_docs:
                logger.info(f"   ✅ Generated: {', '.join(sorted(set(all_successful_docs)))}")
            if all_failed_docs:
                logger.warning(f"   ❌ Failed: {', '.join(sorted(set(all_failed_docs)))}")
                # Log detailed error information for failed tasks
                if "phase2_summary" in results:
                    for failed_task in results["phase2_summary"].get("failed", []):
                        logger.warning(f"      - {failed_task['doc_type']}: {failed_task.get('error', 'Unknown error')}")
            
            logger.info("=" * 80)
            
            # Store final summary in results
            results["execution_summary"] = {
                "total_documents": total_docs,
                "successful_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count / total_docs * 100 if total_docs > 0 else 0,
                "successful_documents": sorted(set(all_successful_docs)),
                "failed_documents": sorted(set(all_failed_docs))
            }
            
            # --- PHASE 4: CODE ANALYSIS AND DOCUMENTATION UPDATE (Optional, Docs-First Mode Only) ---
            # Note: In code-first mode, code analysis was already done in Phase 0
            if workflow_mode == "docs_first" and codebase_path:
                logger.info("=" * 80)
                logger.info("--- PHASE 4: Code Analysis and Documentation Update (Docs-First Mode) ---")
                logger.info("=" * 80)
                logger.info(f"📁 Analyzing codebase at: {codebase_path}")
                
                try:
                    # Analyze codebase
                    logger.info("🔍 Step 1: Analyzing codebase structure...")
                    code_analysis = self.code_analyst.analyze_codebase(codebase_path)
                    logger.info(f"  ✅ Code analysis complete: {len(code_analysis.get('modules', []))} modules, "
                              f"{len(code_analysis.get('classes', []))} classes, "
                              f"{len(code_analysis.get('functions', []))} functions")
                    
                    # Update API Documentation with code analysis
                    logger.info("📝 Step 2: Updating API documentation based on actual code...")
                    try:
                        # Get existing API documentation
                        api_doc_content = final_docs.get(AgentType.API_DOCUMENTATION)
                        
                        # Generate updated API documentation from code
                        updated_api_doc = self.code_analyst.generate_code_documentation(
                            code_analysis=code_analysis,
                            existing_docs=api_doc_content
                        )
                        
                        # Save updated API documentation
                        api_doc_path = document_file_paths.get(AgentType.API_DOCUMENTATION)
                        if api_doc_path:
                            # Update the file
                            if Path(api_doc_path).is_absolute():
                                Path(api_doc_path).write_text(updated_api_doc, encoding='utf-8')
                            else:
                                self.file_manager.write_file(api_doc_path, updated_api_doc)
                            
                            # Update final_docs and context
                            final_docs[AgentType.API_DOCUMENTATION] = updated_api_doc
                            
                            # Update context
                            api_output = AgentOutput(
                                agent_type=AgentType.API_DOCUMENTATION,
                                document_type="api_documentation",
                                content=updated_api_doc,
                                file_path=api_doc_path,
                                status=DocumentStatus.COMPLETE,
                                generated_at=datetime.now(),
                                dependencies=[]
                            )
                            self.context_manager.save_agent_output(project_id, api_output)
                            
                            logger.info(f"  ✅ API documentation updated: {api_doc_path}")
                            results["status"]["api_documentation"] = "updated_with_code_analysis"
                        else:
                            logger.warning("  ⚠️  API documentation file path not found, creating new file")
                            api_doc_path = self.file_manager.write_file("api_documentation.md", updated_api_doc)
                            final_docs[AgentType.API_DOCUMENTATION] = updated_api_doc
                            document_file_paths[AgentType.API_DOCUMENTATION] = api_doc_path
                            results["files"]["api_documentation"] = api_doc_path
                            results["status"]["api_documentation"] = "created_from_code_analysis"
                    except Exception as e:
                        logger.warning(f"  ⚠️  API documentation update failed: {e}")
                    
                    # Update Developer Documentation with code analysis
                    logger.info("📝 Step 3: Updating developer documentation based on actual code...")
                    try:
                        # Get existing developer documentation
                        dev_doc_content = final_docs.get(AgentType.DEVELOPER_DOCUMENTATION)
                        
                        # Generate updated developer documentation from code
                        updated_dev_doc = self.code_analyst.generate_code_documentation(
                            code_analysis=code_analysis,
                            existing_docs=dev_doc_content
                        )
                        
                        # Save updated developer documentation
                        dev_doc_path = document_file_paths.get(AgentType.DEVELOPER_DOCUMENTATION)
                        if dev_doc_path:
                            # Update the file
                            if Path(dev_doc_path).is_absolute():
                                Path(dev_doc_path).write_text(updated_dev_doc, encoding='utf-8')
                            else:
                                self.file_manager.write_file(dev_doc_path, updated_dev_doc)
                            
                            # Update final_docs and context
                            final_docs[AgentType.DEVELOPER_DOCUMENTATION] = updated_dev_doc
                            
                            # Update context
                            dev_output = AgentOutput(
                                agent_type=AgentType.DEVELOPER_DOCUMENTATION,
                                document_type="developer_documentation",
                                content=updated_dev_doc,
                                file_path=dev_doc_path,
                                status=DocumentStatus.COMPLETE,
                                generated_at=datetime.now(),
                                dependencies=[]
                            )
                            self.context_manager.save_agent_output(project_id, dev_output)
                            
                            logger.info(f"  ✅ Developer documentation updated: {dev_doc_path}")
                            results["status"]["developer_documentation"] = "updated_with_code_analysis"
                        else:
                            logger.warning("  ⚠️  Developer documentation file path not found, creating new file")
                            dev_doc_path = self.file_manager.write_file("developer_guide.md", updated_dev_doc)
                            final_docs[AgentType.DEVELOPER_DOCUMENTATION] = updated_dev_doc
                            document_file_paths[AgentType.DEVELOPER_DOCUMENTATION] = dev_doc_path
                            results["files"]["developer_documentation"] = dev_doc_path
                            results["status"]["developer_documentation"] = "created_from_code_analysis"
                    except Exception as e:
                        logger.warning(f"  ⚠️  Developer documentation update failed: {e}")
                    
                    # Save code analysis results
                    logger.info("💾 Step 4: Saving code analysis results...")
                    try:
                        import json
                        code_analysis_json = json.dumps(code_analysis, indent=2, default=str)
                        code_analysis_path = self.file_manager.write_file("code_analysis.json", code_analysis_json)
                        results["files"]["code_analysis"] = code_analysis_path
                        results["status"]["code_analysis"] = "complete"
                        logger.info(f"  ✅ Code analysis saved: {code_analysis_path}")
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to save code analysis: {e}")
                    
                    logger.info("=" * 80)
                    logger.info("✅ PHASE 4 COMPLETE: Code analysis and documentation update completed")
                    logger.info("=" * 80)
                    
                except Exception as e:
                    logger.error(f"  ❌ Phase 4 (Code Analysis) failed: {e}", exc_info=True)
                    results["status"]["code_analysis"] = "failed"
                    results["code_analysis_error"] = str(e)
            elif workflow_mode == "code_first":
                logger.debug("  Phase 4 skipped (code-first mode: code analysis was done in Phase 0)")
            else:
                logger.debug("  Phase 4 skipped (no codebase_path provided)")
            
            # Optional: Auto-Fix Loop (can be enabled via ENABLE_AUTO_FIX=true)
            # Note: In hybrid mode, Phase 1 documents already went through quality gates
            # This auto-fix is primarily for secondary documents if needed
            # (Keeping the auto-fix code for backward compatibility, but it's optional in hybrid mode)
            try:
                from src.config.settings import get_settings
                settings = get_settings()
                
                enable_auto_fix = getattr(settings, 'enable_auto_fix', False) or os.getenv("ENABLE_AUTO_FIX", "false").lower() == "true"
                fix_threshold = float(os.getenv("AUTO_FIX_THRESHOLD", "70.0"))
                
                if enable_auto_fix:
                    logger.info("🔧 Optional Auto-Fix Loop: Analyzing quality review for secondary documents...")
                    quality_review_content = self.file_manager.read_file(quality_review_path)
                    
                    # Extract overall quality score
                    overall_score_pattern = r'Overall Quality Score:\s*(\d+)/100'
                    overall_scores = re.findall(overall_score_pattern, quality_review_content)
                    overall_score = int(overall_scores[0]) if overall_scores else 100
                    
                    # In hybrid mode, we typically don't need auto-fix for Phase 1 documents
                    # (they already went through quality gates), but we can improve Phase 2 documents
                    logger.info(f"  📊 Overall quality score: {overall_score}/100")
                    if overall_score < fix_threshold:
                        logger.info(f"  ⚠️  Overall score below threshold ({fix_threshold}), but Phase 1 documents already have quality gates")
                        logger.info(f"  💡 Consider reviewing quality_review.md for detailed feedback")
                    else:
                        logger.info(f"  ✅ Overall quality score meets threshold")
                else:
                    logger.debug("  Auto-Fix Loop disabled (ENABLE_AUTO_FIX=false)")
            except Exception as e:
                logger.debug(f"  Auto-Fix Loop check skipped: {e}")
            
            # Summary
            logger.info("=" * 80)
            logger.info(f"🚀 HYBRID Workflow COMPLETED for project {project_id}")
            logger.info("=" * 80)
            
            summary = get_documents_summary(results["files"])
            logger.info(f"Documents organized by level: Level 1: {len(summary['level_1_strategic']['documents'])}, "
                       f"Level 2: {len(summary['level_2_product']['documents'])}, "
                       f"Level 3: {len(summary['level_3_technical']['documents'])}, "
                       f"Cross-Level: {len(summary['cross_level']['documents'])}")
            
            results["documents_by_level"] = summary
            
            return results
            
        except Exception as e:
                logger.error(f"❌ CRITICAL ERROR in HYBRID workflow: {str(e)}", exc_info=True)
                results["error"] = str(e)
                return results
    
    async def async_generate_all_docs(
        self,
        user_idea: str,
        project_id: Optional[str] = None,
        profile: str = "team",
        codebase_path: Optional[str] = None,
        workflow_mode: str = "docs_first",
        progress_callback: Optional[Callable[[str, str, str], None]] = None,
        phase1_only: bool = False,
        phases_to_run: Optional[List[int]] = None
    ) -> Dict:
        """
        Generate all documentation types asynchronously (native async implementation)
        
        This is a native async implementation that uses async operations throughout:
        - Phase 0: Code analysis (if code-first mode) - runs in executor (I/O bound)
        - Phase 1: DAG-based parallel execution with quality gates - uses AsyncParallelExecutor
        - Phase 2: DAG-based parallel execution - uses AsyncParallelExecutor
        - Phase 3: Final packaging (cross-ref, review, convert) - uses async I/O
        - Phase 4: Code analysis (if docs-first mode) - runs in executor (I/O bound)
        
        This method provides better performance than the sync version when called from
        async contexts (e.g., FastAPI endpoints) by avoiding thread pool overhead.
        
        Args:
            user_idea: User's project idea
            project_id: Optional project ID (generates one if not provided)
            profile: "team" or "individual" - determines which docs to generate
            codebase_path: Optional path to codebase directory
            workflow_mode: "docs_first" (default) or "code_first" - workflow mode
            progress_callback: Optional async callback for progress updates
                Called with (phase, task_id, status) where:
                - phase: "phase_1", "phase_2", "phase_3", "phase_4", or "phase_5"
                - task_id: Task identifier (e.g., "requirements", "business_model")
                - status: "complete" or "failed"
            phase1_only: If True, only execute Phase 1 and skip all Phase 2+ (default: False)
                Useful for testing or when you want to review Phase 1 results before continuing
            phases_to_run: Optional list of phase numbers to execute (e.g., [2, 3] for Phase 2 and 3 only)
                If None, runs all phases (2-5). Only applies if phase1_only=False.
                Examples:
                - [2] - Only Phase 2 (Technical Foundation)
                - [2, 3] - Phase 2 and 3 (Technical + API/Dev docs)
                - [2, 5] - Phase 2 and 5 (Technical + Business docs)
        
        Returns:
            Dict with generated file paths and status
        """
        # --- SETUP ---
        if not project_id:
            project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        workflow_mode = workflow_mode.lower()
        if workflow_mode not in ["docs_first", "code_first"]:
            logger.warning(f"Invalid workflow_mode '{workflow_mode}', using 'docs_first'")
            workflow_mode = "docs_first"
        
        logger.info(f"🚀 Starting HYBRID Workflow (Async) - Project ID: {project_id}, Profile: {profile}, Mode: {workflow_mode}")
        
        results = {
            "project_id": project_id,
            "user_idea": user_idea,
            "profile": profile,
            "workflow_mode": workflow_mode,
            "files": {},
            "status": {}
        }
        
        # Store final, high-quality document content
        final_docs = {}
        document_file_paths = {}
        
        # Store code analysis results (for code-first mode)
        code_analysis_result = None
        code_analysis_summary = None
        
        try:
            # --- PHASE 0: CODE ANALYSIS (Code-First Mode) ---
            if workflow_mode == "code_first" and codebase_path:
                logger.info("=" * 80)
                logger.info("--- PHASE 0: Code Analysis (Code-First Mode) ---")
                logger.info("=" * 80)
                logger.info(f"📁 Analyzing codebase at: {codebase_path}")
                
                try:
                    # Analyze codebase (I/O bound, run in executor)
                    logger.info("🔍 Analyzing codebase structure...")
                    loop = asyncio.get_event_loop()
                    code_analysis_result = await loop.run_in_executor(
                        None,
                        lambda: self.code_analyst.analyze_codebase(codebase_path)
                    )
                    logger.info(f"  ✅ Code analysis complete: {len(code_analysis_result.get('modules', []))} modules, "
                              f"{len(code_analysis_result.get('classes', []))} classes, "
                              f"{len(code_analysis_result.get('functions', []))} functions")
                    
                    # Generate code analysis summary for use in documentation
                    code_analysis_summary = f"""
# Codebase Analysis Summary

## Modules Analyzed: {len(code_analysis_result.get('modules', []))}
## Classes Found: {len(code_analysis_result.get('classes', []))}
## Functions Found: {len(code_analysis_result.get('functions', []))}

## Key Classes:
"""
                    for cls in code_analysis_result.get('classes', [])[:20]:  # Limit to first 20
                        code_analysis_summary += f"""
### {cls.get('name', 'Unknown')} (in {cls.get('file', 'unknown')})
- Docstring: {cls.get('docstring', 'No docstring')}
- Methods: {len(cls.get('methods', []))}
- Bases: {', '.join(cls.get('bases', []))}
"""
                    
                    code_analysis_summary += "\n## Key Functions:\n"
                    for func in code_analysis_result.get('functions', [])[:20]:  # Limit to first 20
                        code_analysis_summary += f"""
### {func.get('name', 'Unknown')} (in {func.get('file', 'unknown')})
- Docstring: {func.get('docstring', 'No docstring')}
- Args: {', '.join(func.get('args', []))}
"""
                    
                    # Store code analysis in context for use in Phase 1 and Phase 2
                    logger.info("  ✅ Code analysis summary generated for use in documentation generation")
                    results["status"]["code_analysis"] = "complete"
                    results["code_analysis"] = {
                        "modules_count": len(code_analysis_result.get('modules', [])),
                        "classes_count": len(code_analysis_result.get('classes', [])),
                        "functions_count": len(code_analysis_result.get('functions', []))
                    }
                    
                except Exception as e:
                    logger.error(f"  ❌ Phase 0 (Code Analysis) failed: {e}", exc_info=True)
                    results["status"]["code_analysis"] = "failed"
                    results["code_analysis_error"] = str(e)
                    # Continue with docs-first mode if code analysis fails
                    logger.warning("  ⚠️  Continuing with docs-first mode (code analysis failed)")
                    workflow_mode = "docs_first"
                    code_analysis_result = None
                    code_analysis_summary = None
            
            # --- PHASE 1: FOUNDATIONAL DOCUMENTS (DAG with Quality Gate) ---
            logger.info("=" * 80)
            logger.info("--- PHASE 1: Generating Foundational Documents (DAG with Quality Gate) ---")
            logger.info("=" * 80)
            
            # Get Phase 1 task configurations from DAG
            phase1_tasks = get_phase1_tasks_for_profile(profile=profile)
            logger.info(f"📋 Phase 1 DAG: {len(phase1_tasks)} tasks for profile '{profile}'")
            
            # Build dependency map
            phase1_dependency_map = build_phase1_task_dependencies(phase1_tasks)
            
            # Create async executor for Phase 1
            executor = AsyncParallelExecutor(max_workers=4)  # Smaller pool for Phase 1
            
            # Create async task execution coroutines for each Phase 1 task
            def create_phase1_task_coro(task: Phase1Task):
                """Create an async task coroutine that executes Phase 1 task with quality gate"""
                async def execute_phase1_task():
                    # Get dependencies from context (AsyncParallelExecutor ensures dependencies are completed first)
                    deps_content: Dict[AgentType, str] = {}
                    
                    for dep_type in task.dependencies:
                        dep_type_capture = dep_type
                        # Context manager calls are sync, so run in executor
                        loop = asyncio.get_event_loop()
                        dep_output = await loop.run_in_executor(
                            None,
                            lambda dt=dep_type_capture: self.context_manager.get_agent_output(project_id, dt)
                        )
                        if dep_output:
                            deps_content[dep_type] = dep_output.content
                        else:
                            # Optional dependencies (like PROJECT_CHARTER for individual profile) may be None
                            logger.debug(f"  ℹ️  Phase 1 dependency {dep_type.value} not found in context for {task.task_id} (may be optional)")
                            deps_content[dep_type] = None
                    
                    # Build kwargs for agent.generate_and_save
                    # Pass code_analysis_summary if available (code-first mode)
                    kwargs = build_kwargs_for_phase1_task(
                        task=task,
                        user_idea=user_idea,
                        project_id=project_id,
                        context_manager=self.context_manager,
                        deps_content=deps_content,
                        code_analysis_summary=code_analysis_summary  # Pass code analysis for code-first mode
                    )
                    
                    # Get agent instance
                    agent = get_agent_for_phase1_task(self, task.agent_type)
                    if not agent:
                        raise ValueError(f"Agent not found for {task.agent_type.value}")
                    
                    # Set phase number for phase-based model selection
                    agent._current_phase_number = 1
                    
                    # Execute with quality gate (async version)
                    logger.info(f"🔍 Executing Phase 1 task {task.task_id} with quality gate (threshold: {task.quality_threshold})...")
                    file_path, content = await self._async_run_agent_with_quality_loop(
                        agent_instance=agent,
                        agent_type=task.agent_type,
                        generate_kwargs=kwargs,
                        output_filename=None,  # Will be extracted from kwargs
                        project_id=None,  # Will be extracted from kwargs
                        quality_threshold=task.quality_threshold
                    )
                    
                    # Result is automatically saved to context by _async_run_agent_with_quality_loop
                    logger.info(f"✅ Phase 1 task {task.task_id} completed: {len(content)} characters")
                    return file_path, content
                
                return execute_phase1_task
            
            # Note: Phase 1 tasks are now executed SEQUENTIALLY with per-document approval
            # The create_phase1_task_coro function is kept for potential future use but not used here
            # because we need sequential execution with approval workflow
            
            # Execute Phase 1 tasks SEQUENTIALLY with per-document approval
            # Each document is generated, checked for quality, and then waits for user approval
            logger.info("🚀 Executing Phase 1 tasks SEQUENTIALLY (with per-document approval)...")
            
            # Sort tasks by dependencies to ensure correct execution order
            def get_task_order(tasks: List) -> List:
                """Sort tasks by dependency order (topological sort)"""
                ordered = []
                visited = set()
                
                def visit(task):
                    if task.task_id in visited:
                        return
                    visited.add(task.task_id)
                    # Visit dependencies first
                    for dep_type in task.dependencies:
                        # Find dependent task
                        for t in tasks:
                            if t.agent_type == dep_type:
                                visit(t)
                                break
                    ordered.append(task)
                
                for task in tasks:
                    visit(task)
                return ordered
            
            ordered_phase1_tasks = get_task_order(phase1_tasks)
            phase1_task_results = {}
            
            # Execute each task sequentially and wait for approval
            for task_idx, task in enumerate(ordered_phase1_tasks, 1):
                logger.info(f"📝 [{task_idx}/{len(ordered_phase1_tasks)}] Generating {task.task_id}...")
                
                # Get dependencies from context
                deps_content: Dict[AgentType, str] = {}
                for dep_type in task.dependencies:
                    loop = asyncio.get_event_loop()
                    dep_output = await loop.run_in_executor(
                        None,
                        lambda dt=dep_type: self.context_manager.get_agent_output(project_id, dt)
                    )
                    if dep_output:
                        deps_content[dep_type] = dep_output.content
                
                # Build kwargs
                kwargs = build_kwargs_for_phase1_task(
                    task=task,
                    user_idea=user_idea,
                    project_id=project_id,
                    context_manager=self.context_manager,
                    deps_content=deps_content,
                    code_analysis_summary=code_analysis_summary
                )
                
                # Get agent instance
                agent = get_agent_for_phase1_task(self, task.agent_type)
                if not agent:
                    raise ValueError(f"Agent not found for {task.agent_type.value}")
                
                agent._current_phase_number = 1
                
                # Execute with quality gate (async version)
                logger.info(f"🔍 Executing {task.task_id} with quality gate (threshold: {task.quality_threshold})...")
                file_path, content = await self._async_run_agent_with_quality_loop(
                    agent_instance=agent,
                    agent_type=task.agent_type,
                    generate_kwargs=kwargs,
                    output_filename=None,
                    project_id=project_id,
                    quality_threshold=task.quality_threshold
                )
                
                # Store result
                phase1_task_results[task.task_id] = (file_path, content)
                
                # Map task_id to document display name
                doc_name_map = {
                    "requirements": "Requirements",
                    "project_charter": "Project Charter",
                    "user_stories": "User Stories",
                    "business_model": "Business Model",
                    "marketing_plan": "Marketing Plan",
                    "pm_doc": "PM Documentation",
                    "stakeholder_doc": "Stakeholder Communication",
                    "wbs": "Work Breakdown Structure",
                    "technical_doc": "Technical Specification",
                }
                doc_name = doc_name_map.get(task.task_id, task.task_id.replace("_", " ").title())
                
                # Send progress update
                if progress_callback:
                    await progress_callback("phase_1", doc_name, "complete")
                
                # Update status to indicate this document is ready for review
                doc_type_map = {
                    AgentType.REQUIREMENTS_ANALYST: "requirements",
                    AgentType.TECHNICAL_DOCUMENTATION: "technical_documentation",
                }
                doc_type = doc_type_map.get(task.agent_type, task.agent_type.value)
                
                # Update status for this specific document
                self.context_manager.update_project_status(
                    project_id=project_id,
                    status=f"phase1_document_ready:{doc_type}",
                    completed_agents=[doc_type],
                    results=results
                )
                
                # Wait for user approval of this specific document with regeneration on rejection
                logger.info(f"⏸️  {doc_name} generated and ready for review (quality score >= {task.quality_threshold})")
                logger.info(f"⏳ Waiting for user approval of {doc_name}...")
                
                # Poll for approval of this specific document
                max_wait_time = 3600  # 1 hour timeout
                check_interval = 2  # Check every 2 seconds
                max_regeneration_attempts = 3  # Maximum regeneration attempts after rejection
                regeneration_attempts = 0
                loop = asyncio.get_event_loop()
                
                while regeneration_attempts < max_regeneration_attempts:
                    waited_time = 0
                    approved = False
                    
                    # Wait for approval/rejection
                    while waited_time < max_wait_time:
                        try:
                            # Run database check in executor to avoid blocking event loop
                            approval_status = await loop.run_in_executor(
                                None,
                                lambda: self.context_manager.is_document_approved(project_id, task.agent_type)
                            )
                            
                            if approval_status is True:
                                logger.info(f"✅ {doc_name} APPROVED by user - breaking out of approval loop...")
                                approved = True
                                break
                            elif approval_status is False:
                                logger.info(f"❌ {doc_name} REJECTED by user - will regenerate (attempt {regeneration_attempts + 1}/{max_regeneration_attempts})")
                                # New version will be created with pending status, so we don't need to clear rejection
                                # The rejection status on the old version won't affect the new version
                                await asyncio.sleep(1)  # Brief pause before regeneration
                                break  # Break out of approval waiting loop to regenerate
                            else:
                                # Still pending, wait and check again
                                if waited_time % 10 == 0:  # Log every 10 seconds
                                    logger.debug(f"⏳ Still waiting for approval of {doc_name}... (waited {waited_time}s)")
                                await asyncio.sleep(check_interval)
                                waited_time += check_interval
                                
                                # Send periodic WebSocket updates
                                if progress_callback and waited_time % 10 == 0:
                                    await progress_callback("phase_1", doc_name, "awaiting_approval")
                        except Exception as e:
                            logger.error(f"Error checking approval status for {doc_name}: {e}", exc_info=True)
                            # Continue waiting despite error
                            await asyncio.sleep(check_interval)
                            waited_time += check_interval
                    
                    # Check if approved
                    if approved:
                        break
                    
                    # Check if we timed out
                    if waited_time >= max_wait_time:
                        logger.warning(f"⏰ Approval timeout for {doc_name} after {max_wait_time} seconds")
                        results["status"][doc_type] = "approval_timeout"
                        results["error"] = f"{doc_name} approval timeout after {max_wait_time} seconds"
                        self.context_manager.update_project_status(
                            project_id=project_id,
                            status=f"phase1_document_timeout:{doc_type}",
                            results=results
                        )
                        return results
                    
                        # Document was rejected, regenerate
                    regeneration_attempts += 1
                    if regeneration_attempts >= max_regeneration_attempts:
                        logger.error(f"❌ {doc_name} rejected {max_regeneration_attempts} times - stopping workflow")
                        results["status"][doc_type] = "rejected_after_retries"
                        results["error"] = f"{doc_name} was rejected {max_regeneration_attempts} times and regeneration limit reached"
                        await loop.run_in_executor(
                            None,
                            lambda: self.context_manager.update_project_status(
                                project_id=project_id,
                                status=f"phase1_document_rejected_after_retries:{doc_type}",
                                results=results
                            )
                        )
                        return results
                    
                    # Regenerate the document
                    logger.info(f"🔄 Regenerating {doc_name} (attempt {regeneration_attempts}/{max_regeneration_attempts})...")
                    
                    # Send progress update
                    if progress_callback:
                        await progress_callback("phase_1", doc_name, "regenerating")
                    
                    # Re-execute with quality gate (async version)
                    # This will create a new version with pending approval status (approved=0)
                    # The new version will be independent of the rejected version
                    logger.info(f"🔍 Re-executing {task.task_id} with quality gate (threshold: {task.quality_threshold})...")
                    file_path, content = await self._async_run_agent_with_quality_loop(
                        agent_instance=agent,
                        agent_type=task.agent_type,
                        generate_kwargs=kwargs,
                        output_filename=None,
                        project_id=project_id,
                        quality_threshold=task.quality_threshold
                    )
                    
                    # Update result with regenerated content
                    phase1_task_results[task.task_id] = (file_path, content)
                    
                    # Update status for regenerated document
                    await loop.run_in_executor(
                        None,
                        lambda: self.context_manager.update_project_status(
                            project_id=project_id,
                            status=f"phase1_document_ready:{doc_type}",
                            completed_agents=[doc_type],
                            results=results
                        )
                    )
                    
                    # Send progress update
                    if progress_callback:
                        await progress_callback("phase_1", doc_name, "complete")
                    
                    logger.info(f"✅ {doc_name} regenerated - waiting for approval again...")
                    logger.info(f"⏳ Waiting for user approval of {doc_name} (regenerated)...")
                
                # Document approved, continue to next
                logger.info(f"✅ {doc_name} approved - proceeding to next document...")
                logger.info(f"🔄 Continuing workflow loop - {len(ordered_phase1_tasks)} total tasks, {len(phase1_task_results)} completed")
            
            # Process Phase 1 results and update results dictionary
            req_content = None
            charter_content = None
            stories_content = None
            business_model_content = None
            marketing_plan_content = None
            tech_content = None
            db_content = None
            
            for task in phase1_tasks:
                task_result = phase1_task_results.get(task.task_id)
                if task_result:
                    if isinstance(task_result, tuple) and len(task_result) == 2:
                        file_path, content = task_result
                    else:
                        # Handle case where result might be different format
                        logger.warning(f"Unexpected result format for {task.task_id}: {type(task_result)}")
                        continue
                    
                    # Map agent_type to doc_type for results storage
                    doc_type = AGENT_TYPE_TO_DOC_TYPE_PHASE1.get(task.agent_type, task.agent_type.value)
                    
                    # Update results dictionary
                    results["files"][doc_type] = file_path
                    results["status"][doc_type] = "complete_v2"
                    
                    # Store content for later use
                    final_docs[task.agent_type] = content
                    document_file_paths[task.agent_type] = file_path
                    
                    # Keep track of specific documents for validation
                    if task.agent_type == AgentType.REQUIREMENTS_ANALYST:
                        req_content = content
                    elif task.agent_type == AgentType.PROJECT_CHARTER:
                        charter_content = content
                    elif task.agent_type == AgentType.USER_STORIES:
                        stories_content = content
                    elif task.agent_type == AgentType.TECHNICAL_DOCUMENTATION:
                        tech_content = content
                    elif task.agent_type == AgentType.DATABASE_SCHEMA:
                        db_content = content
                else:
                    logger.error(f"❌ Phase 1 task {task.task_id} failed or returned no result")
                    # Mark as failed in status
                    doc_type = AGENT_TYPE_TO_DOC_TYPE_PHASE1.get(task.agent_type, task.agent_type.value)
                    results["status"][doc_type] = "failed"
            
            # Verify requirements were generated
            if not req_content:
                raise ValueError("Requirements not generated in Phase 1")
            
            # Get requirements summary from context (async)
            loop = asyncio.get_event_loop()
            context = await loop.run_in_executor(
                None,
                lambda: self.context_manager.get_shared_context(project_id)
            )
            if not context.requirements:
                raise ValueError("Requirements not found in context after generation")
            
            req_summary = context.get_requirements_summary()
            
            logger.info("=" * 80)
            logger.info("✅ PHASE 1 COMPLETE: Foundational documents generated with quality gates (DAG)")
            logger.info("=" * 80)
            
            # Update status to indicate Phase 1 is complete and awaiting approval
            self.context_manager.update_project_status(
                project_id=project_id,
                status="phase1_complete_awaiting_approval",
                completed_agents=list(results.get("files", {}).keys()),
                results=results
            )
            
            # Send WebSocket update for Phase 1 completion
            if progress_callback:
                await progress_callback("phase_1", "all", "complete")
            
            # Check if Phase 1 is approved (wait for approval if not)
            logger.info("=" * 80)
            logger.info("⏸️  PHASE 1 AWAITING USER APPROVAL")
            logger.info("=" * 80)
            logger.info("📋 Phase 1 documents generated:")
            logger.info("   - requirements.md")
            logger.info("   - technical_spec.md")
            logger.info("")
            logger.info("⏳ Waiting for user approval to proceed to Phase 2...")
            logger.info("   (Use API endpoint /api/approve-phase1/{project_id} to approve)")
            
            # Poll for approval (with timeout)
            max_wait_time = 3600  # 1 hour timeout
            check_interval = 2  # Check every 2 seconds
            waited_time = 0
            
            while waited_time < max_wait_time:
                approval_status = self.context_manager.is_phase1_approved(project_id)
                
                if approval_status is True:
                    logger.info("✅ Phase 1 APPROVED by user - proceeding to Phase 2+")
                    break
                elif approval_status is False:
                    logger.info("❌ Phase 1 REJECTED by user - stopping workflow")
                    results["status"]["phase1_approval"] = "rejected"
                    results["error"] = "Phase 1 documents were rejected by user"
                    self.context_manager.update_project_status(
                        project_id=project_id,
                        status="phase1_rejected",
                        results=results
                    )
                    return results
                else:
                    # Still pending, wait and check again
                    await asyncio.sleep(check_interval)
                    waited_time += check_interval
                    
                    # Send periodic WebSocket updates
                    if progress_callback and waited_time % 10 == 0:  # Every 10 seconds
                        await progress_callback("phase_1", "approval", "pending")
            
            # Check if we timed out
            if waited_time >= max_wait_time:
                logger.warning(f"⏰ Approval timeout after {max_wait_time} seconds - stopping workflow")
                results["status"]["phase1_approval"] = "timeout"
                results["error"] = f"Phase 1 approval timeout after {max_wait_time} seconds"
                self.context_manager.update_project_status(
                    project_id=project_id,
                    status="phase1_approval_timeout",
                    results=results
                )
                return results
            
            logger.info("=" * 80)
            logger.info("🚀 PROCEEDING TO PHASE 2+ (Phase 1 approved)")
            logger.info("=" * 80)
            
            # Check if we should skip Phase 2
            if phase1_only:
                logger.info("=" * 80)
                logger.info("⏸️  PHASE 2 SKIPPED: phase1_only=True - Stopping after Phase 1")
                logger.info("=" * 80)
                
                # Send WebSocket update if callback is available
                if progress_callback:
                    await progress_callback("phase_1", "all", "complete")
                
                # Return results with Phase 1 only
                results["phase1_only"] = True
                results["phase2_summary"] = {
                    "skipped": True,
                    "message": "Phase 2 skipped due to phase1_only=True"
                }
                
                # Skip to Phase 3 (final packaging) or return early
                # For now, we'll skip Phase 2 and Phase 3, return Phase 1 results
                return results
            
            # Get technical summary and database schema for Phase 2
            technical_summary = tech_content
            database_schema_summary = db_content
            
            # Determine which phases to run
            if phases_to_run is None:
                # Get available phases for the profile
                available_phases = get_available_phases(profile=profile)
                phases_to_run = available_phases
            else:
                # Validate phases_to_run
                available_phases = get_available_phases(profile=profile)
                phases_to_run = [p for p in phases_to_run if p in available_phases]
                if not phases_to_run:
                    logger.warning(f"No valid phases to run. Available phases: {available_phases}")
                    return results
            
            logger.info(f"📋 Will execute phases: {phases_to_run} for profile '{profile}'")
            
            # Prepare Phase 1 content for dependency extraction (used across all phases)
            phase1_deps_content = {
                AgentType.REQUIREMENTS_ANALYST: req_content,
                AgentType.TECHNICAL_DOCUMENTATION: technical_summary,
                AgentType.DATABASE_SCHEMA: database_schema_summary,
                AgentType.PROJECT_CHARTER: charter_content if charter_content else None,
                AgentType.USER_STORIES: stories_content,
                AgentType.BUSINESS_MODEL: business_model_content if business_model_content else None,
                AgentType.MARKETING_PLAN: marketing_plan_content if marketing_plan_content else None,
            }
            
            # Phase descriptions for logging
            phase_descriptions = {
                2: "Technical Foundation Documents",
                3: "API and Development Documents",
                4: "User/Support and Project Management Documents"
            }
            
            # Execute phases sequentially (2, 3, 4)
            all_successful_tasks = []
            all_failed_tasks = []
            
            for phase_num in sorted(phases_to_run):
                phase_name = f"PHASE {phase_num}"
                phase_key = f"phase_{phase_num}"
                phase_desc = phase_descriptions.get(phase_num, f"Phase {phase_num} Documents")
                
                logger.info("=" * 80)
                logger.info(f"--- {phase_name}: {phase_desc} (Parallel DAG) ---")
                logger.info("=" * 80)
                
                # Get tasks for this phase
                phase_tasks = get_tasks_for_phase(profile=profile, phase_number=phase_num)
                logger.info(f"📋 {phase_name} DAG: {len(phase_tasks)} tasks for profile '{profile}'")
                
                if not phase_tasks:
                    logger.info(f"⏭️  {phase_name}: No tasks for this phase, skipping...")
                    continue
                
                # Build dependency map (AgentType -> task_id dependencies)
                dependency_map = build_task_dependencies(phase_tasks)
                
                # Create async executor for this phase
                executor = AsyncParallelExecutor(max_workers=8)
            
                # Create async task execution coroutines for this phase
                def create_async_task_coro(task: Phase2Task):
                    """Create an async task coroutine that extracts dependencies and executes agent"""
                    async def execute_async_task():
                        # Extract dependency content from context (for dependencies from previous phases)
                        deps_content = phase1_deps_content.copy()
                        
                        # Get dependencies from context (async-safe)
                        loop = asyncio.get_event_loop()
                        for dep_type in task.dependencies:
                            if dep_type not in deps_content:
                                dep_type_capture = dep_type
                                dep_output = await loop.run_in_executor(
                                    None,
                                    lambda dt=dep_type_capture: self.context_manager.get_agent_output(project_id, dt)
                                )
                                if dep_output:
                                    deps_content[dep_type] = dep_output.content
                                else:
                                    logger.warning(f"  ⚠️  Dependency {dep_type.value} not found in context for {task.task_id}")
                                    deps_content[dep_type] = None
                        
                        # Build kwargs for agent.generate_and_save
                        kwargs = build_kwargs_for_task(
                            task=task,
                            coordinator=self,
                            req_summary=req_summary,
                            technical_summary=technical_summary,
                            charter_content=charter_content,
                            project_id=project_id,
                            context_manager=self.context_manager,
                            deps_content=deps_content,
                            code_analysis_summary=code_analysis_summary  # Pass code analysis for code-first mode
                        )
                        
                        # Apply folder prefix to output_filename based on agent type
                        if "output_filename" in kwargs:
                            kwargs["output_filename"] = get_output_filename_for_agent(task.agent_type, kwargs["output_filename"])
                        
                        # Get agent instance
                        agent = get_agent_for_task(self, task.agent_type)
                        if not agent:
                            raise ValueError(f"Agent not found for {task.agent_type.value}")
                        
                        # Set phase number for phase-based model selection
                        agent._current_phase_number = phase_num
                        
                        # Execute agent.generate_and_save (async if available, otherwise sync in executor)
                        if hasattr(agent, 'async_generate_and_save') and asyncio.iscoroutinefunction(agent.async_generate_and_save):
                            # Native async method (best performance)
                            result = await agent.async_generate_and_save(**kwargs)
                        elif hasattr(agent, 'generate_and_save') and asyncio.iscoroutinefunction(agent.generate_and_save):
                            # Async generate_and_save method
                            result = await agent.generate_and_save(**kwargs)
                        else:
                            # Fallback: run sync method in executor
                            result = await loop.run_in_executor(
                                None,
                                lambda kw=kwargs: agent.generate_and_save(**kw)
                            )
                        return result
                    
                    return execute_async_task
            
                # Add all tasks for this phase to async executor
                for task in phase_tasks:
                    task_coro = create_async_task_coro(task)()
                    dep_task_ids = dependency_map.get(task.task_id, [])
                    
                    executor.add_task(
                        task_id=task.task_id,
                        coro=task_coro,
                        dependencies=dep_task_ids
                    )
                    logger.debug(f"  📝 Added {phase_name} async task: {task.task_id} (depends on: {dep_task_ids})")
                
                # Execute parallel tasks asynchronously (native async)
                logger.info(f"🚀 Executing {len(executor.tasks)} parallel async tasks for {phase_name} with DAG dependencies...")
                
                # Create progress callback wrapper for this phase
                async def phase_progress_callback(completed_count: int, total_count: int, task_id: str):
                    """Wrapper to convert executor callback to our format"""
                    if progress_callback:
                        # Find the task to get its agent_type for display name
                        task = next((t for t in phase_tasks if t.task_id == task_id), None)
                        if task:
                            # Map task_id to document display name
                            doc_name_map = {
                                "technical_doc": "Technical Documentation",
                                "database_schema": "Database Schema",
                                "api_doc": "API Documentation",
                                "setup_guide": "Setup Guide",
                                "dev_doc": "Developer Documentation",
                                "test_doc": "Test Plan",
                                "user_doc": "User Guide",
                                "legal_doc": "Legal Compliance",
                                "support_playbook": "Support Playbook",
                                "pm_doc": "Project Plan",
                                "stakeholder_doc": "Stakeholder Summary",
                                "business_model": "Business Model",
                                "marketing_plan": "Marketing Plan",
                            }
                            doc_name = doc_name_map.get(task_id, task_id.replace("_", " ").title())
                            await progress_callback(phase_key, doc_name, "complete")
                
                parallel_results = await executor.execute(progress_callback=phase_progress_callback)
                
                # Collect parallel task results with resilient error handling
                successful_tasks = []
                failed_tasks = []
                
                # Helper function to convert AgentType to doc_type
                agent_type_to_doc_type = {
                    AgentType.TECHNICAL_DOCUMENTATION: "technical_documentation",
                    AgentType.DATABASE_SCHEMA: "database_schema",
                    AgentType.API_DOCUMENTATION: "api_documentation",
                    AgentType.SETUP_GUIDE: "setup_guide",
                    AgentType.DEVELOPER_DOCUMENTATION: "developer_documentation",
                    AgentType.TEST_DOCUMENTATION: "test_documentation",
                    AgentType.USER_DOCUMENTATION: "user_documentation",
                    AgentType.LEGAL_COMPLIANCE: "legal_compliance",
                    AgentType.SUPPORT_PLAYBOOK: "support_playbook",
                    AgentType.PM_DOCUMENTATION: "pm_documentation",
                    AgentType.STAKEHOLDER_COMMUNICATION: "stakeholder_communication",
                    AgentType.BUSINESS_MODEL: "business_model",
                    AgentType.MARKETING_PLAN: "marketing_plan",
                }
                
                def get_doc_type_from_agent_type(agent_type: AgentType) -> str:
                    """Convert AgentType to document type name for results"""
                    return agent_type_to_doc_type.get(agent_type, agent_type.value)
                
                for task in phase_tasks:
                    task_id = task.task_id
                    file_path = parallel_results.get(task_id)
                    agent_type = task.agent_type
                    doc_type = get_doc_type_from_agent_type(agent_type)
                    
                    # Check task status from executor
                    task_status = executor.tasks.get(task_id)
                    if task_status and task_status.status == AsyncTaskStatus.FAILED:
                        # Task failed - record error but continue processing other tasks
                        error = task_status.error if task_status.error else "Unknown error"
                        error_msg = str(error) if error else "Unknown error"
                        logger.error(f"  ❌ Task {task_id} ({doc_type}) failed: {error_msg}")
                        results["status"][doc_type] = "failed"
                        failed_tasks.append({
                            "task_id": task_id,
                            "doc_type": doc_type,
                            "agent_type": agent_type.value,
                            "error": error_msg
                        })
                    elif file_path and task_status and task_status.status == AsyncTaskStatus.COMPLETE:
                        # Task succeeded
                        results["files"][doc_type] = file_path
                        results["status"][doc_type] = "complete"
                        
                        # Read content and add to final_docs (async I/O)
                        try:
                            loop = asyncio.get_event_loop()
                            content = await loop.run_in_executor(
                                None,
                                lambda fp=file_path: self.file_manager.read_file(fp)
                            )
                            final_docs[agent_type] = content
                            document_file_paths[agent_type] = file_path
                            logger.info(f"  ✅ {doc_type}: {file_path}")
                            successful_tasks.append({
                                "task_id": task_id,
                                "doc_type": doc_type,
                                "agent_type": agent_type.value,
                                "file_path": file_path
                            })
                        except Exception as e:
                            logger.warning(f"  ⚠️  Could not read {doc_type}: {e}")
                            results["status"][doc_type] = "failed"
                            failed_tasks.append({
                                "task_id": task_id,
                                "doc_type": doc_type,
                                "agent_type": agent_type.value,
                                "error": f"Failed to read file: {str(e)}"
                            })
                    else:
                        # Task status unknown or incomplete
                        logger.warning(f"  ⚠️  Task {task_id} ({doc_type}) has unknown status")
                        results["status"][doc_type] = "unknown"
                        failed_tasks.append({
                            "task_id": task_id,
                            "doc_type": doc_type,
                            "agent_type": agent_type.value,
                            "error": "Task status unknown or incomplete"
                        })
                
                # Log phase summary
                logger.info("=" * 80)
                logger.info(f"✅ {phase_name} COMPLETE: {len(successful_tasks)}/{len(phase_tasks)} documents generated successfully")
                if successful_tasks:
                    logger.info(f"   ✅ Successful: {', '.join([t['doc_type'] for t in successful_tasks])}")
                if failed_tasks:
                    logger.warning(f"   ❌ Failed: {', '.join([t['doc_type'] for t in failed_tasks])}")
                    for failed_task in failed_tasks:
                        logger.warning(f"      - {failed_task['doc_type']}: {failed_task.get('error', 'Unknown error')}")
                logger.info("=" * 80)
                
                # Accumulate results across all phases
                all_successful_tasks.extend(successful_tasks)
                all_failed_tasks.extend(failed_tasks)
            
            # Store overall task execution summary in results
            results["phase2_summary"] = {
                "successful": all_successful_tasks,
                "failed": all_failed_tasks,
                "total": len(all_successful_tasks) + len(all_failed_tasks),
                "success_count": len(all_successful_tasks),
                "failed_count": len(all_failed_tasks),
                "phases_executed": phases_to_run
            }
            
            # --- PHASE 3: FINAL PACKAGING (Cross-ref, Review, Convert) ---
            logger.info("=" * 80)
            logger.info("--- PHASE 3: Final Packaging and Conversion ---")
            logger.info("=" * 80)
            
            # 1. Cross-Referencing (async I/O)
            logger.info("📎 Step 1: Adding cross-references to all documents...")
            try:
                loop = asyncio.get_event_loop()
                referenced_docs = await loop.run_in_executor(
                    None,
                    lambda: self.cross_referencer.create_cross_references(
                        final_docs,
                        document_file_paths
                    )
                )
                
                # Save cross-referenced documents back to files (async I/O)
                updated_count = 0
                for agent_type, referenced_content in referenced_docs.items():
                    original_content = final_docs.get(agent_type)
                    if referenced_content != original_content:
                        original_file_path = document_file_paths[agent_type]
                        # Write directly to original absolute path to preserve folder structure (async I/O)
                        if Path(original_file_path).is_absolute():
                            await loop.run_in_executor(
                                None,
                                lambda fp=original_file_path, cnt=referenced_content: Path(fp).write_text(cnt, encoding='utf-8')
                            )
                            logger.debug(f"Updated cross-referenced file: {original_file_path}")
                        else:
                            await loop.run_in_executor(
                                None,
                                lambda fp=original_file_path, cnt=referenced_content: self.file_manager.write_file(fp, cnt)
                            )
                        # Update final_docs for quality review
                        final_docs[agent_type] = referenced_content
                        updated_count += 1
                
                logger.info(f"  ✅ Added cross-references to {updated_count} documents")
                
                # Generate document index (async I/O)
                try:
                    loop = asyncio.get_event_loop()
                    index_content = await loop.run_in_executor(
                        None,
                        lambda: self.cross_referencer.generate_document_index(
                            final_docs,
                            document_file_paths,
                            project_name=req_summary.get('project_overview', 'Project')[:50]
                        )
                    )
                    index_path = await loop.run_in_executor(
                        None,
                        lambda cnt=index_content: self.file_manager.write_file("index.md", cnt)
                    )
                    results["files"]["document_index"] = index_path
                    logger.info(f"  ✅ Document index created: {index_path}")
                except Exception as e:
                    logger.warning(f"  ⚠️  Could not generate index: {e}")
            except Exception as e:
                logger.warning(f"  ⚠️  Cross-referencing failed: {e}")
            
            # 2. Final Quality Review (generate report only) (async I/O)
            logger.info("📊 Step 2: Generating final quality review report...")
            try:
                # Convert final_docs to dict with string keys for quality reviewer
                all_documentation_for_review = {
                    agent_type.value: content
                    for agent_type, content in final_docs.items()
                }
                
                loop = asyncio.get_event_loop()
                quality_review_path = await loop.run_in_executor(
                    None,
                    lambda: self.quality_reviewer.generate_and_save(
                        all_documentation=all_documentation_for_review,
                        output_filename="quality_review.md",
                        project_id=project_id,
                        context_manager=self.context_manager
                    )
                )
                results["files"]["quality_review"] = quality_review_path
                results["status"]["quality_review"] = "complete"
                logger.info(f"  ✅ Quality review report generated: {quality_review_path}")
            except Exception as e:
                logger.warning(f"  ⚠️  Quality review failed: {e}")
                results["status"]["quality_review"] = "failed"
            
            # 3. Claude CLI Documentation (async I/O)
            logger.info("📝 Step 3: Generating Claude CLI documentation...")
            try:
                loop = asyncio.get_event_loop()
                claude_md_path = await loop.run_in_executor(
                    None,
                    lambda: self.claude_cli_agent.generate_and_save(
                        all_documentation=final_docs,
                        project_id=project_id,
                        context_manager=self.context_manager
                    )
                )
                results["files"]["claude_cli_documentation"] = claude_md_path
                results["status"]["claude_cli_documentation"] = "complete"
                logger.info(f"  ✅ Claude CLI documentation generated: {claude_md_path}")
            except Exception as e:
                logger.warning(f"  ⚠️  Claude CLI documentation generation failed: {e}")
                results["status"]["claude_cli_documentation"] = "failed"
            
            # 4. Format Conversion (async I/O)
            logger.info("📄 Step 4: Converting documents to multiple formats...")
            try:
                # Prepare documents for conversion
                documents_for_conversion = {
                    agent_type.value: content
                    for agent_type, content in final_docs.items()
                }
                
                loop = asyncio.get_event_loop()
                format_results = await loop.run_in_executor(
                    None,
                    lambda: self.format_converter.convert_all_documents(
                        documents=documents_for_conversion,
                        formats=["html", "pdf", "docx"],
                        project_id=project_id,
                        context_manager=self.context_manager
                    )
                )
                results["files"]["format_conversions"] = format_results
                
                # Analyze conversion results to determine overall status
                total_docs = len(format_results)
                successful_formats = {}
                failed_formats = {}
                
                for doc_name, doc_results in format_results.items():
                    for fmt, fmt_result in doc_results.items():
                        if isinstance(fmt_result, dict) and fmt_result.get("status") == "success":
                            successful_formats[fmt] = successful_formats.get(fmt, 0) + 1
                        else:
                            failed_formats[fmt] = failed_formats.get(fmt, 0) + 1
                
                # Count successful conversions
                total_successful = sum(successful_formats.values())
                total_attempted = total_docs * 3  # 3 formats per document
                
                if total_successful == total_attempted:
                    results["status"]["format_conversions"] = "complete"
                    logger.info(f"  ✅ Converted {total_docs} documents to {total_successful} files (HTML, PDF, DOCX)")
                elif total_successful > 0:
                    results["status"]["format_conversions"] = f"partial ({total_successful}/{total_attempted} successful)"
                    logger.info(f"  ⚠️  Format conversion partial: {total_successful}/{total_attempted} successful")
                    # Log failed formats for debugging
                    for fmt, count in failed_formats.items():
                        logger.warning(f"    - {fmt.upper()}: {count} failures")
                else:
                    results["status"]["format_conversions"] = "failed"
                    logger.warning(f"  ❌ Format conversion failed: all {total_attempted} conversions failed")
                
                # Store conversion status details for frontend
                results["format_conversion_status"] = {
                    "successful": successful_formats,
                    "failed": failed_formats,
                    "total_docs": total_docs,
                    "total_successful": total_successful,
                    "total_attempted": total_attempted
                }
                
            except Exception as e:
                logger.error(f"  ❌ Format conversion failed with exception: {e}", exc_info=True)
                results["status"]["format_conversions"] = "failed"
                results["format_conversion_status"] = {
                    "error": str(e),
                    "successful": {},
                    "failed": {},
                    "total_docs": 0,
                    "total_successful": 0,
                    "total_attempted": 0
                }
            
            logger.info("=" * 80)
            logger.info("✅ PHASE 3 COMPLETE: Final packaging and conversion completed")
            logger.info("=" * 80)
            
            # Generate final execution summary report
            logger.info("=" * 80)
            logger.info("📊 FINAL EXECUTION SUMMARY")
            logger.info("=" * 80)
            
            # Count successful and failed documents across all phases
            all_successful_docs = []
            all_failed_docs = []
            
            # Phase 1 documents (from results["status"])
            # NOTE: technical_documentation and database_schema have been moved to Phase 2 for parallel execution
            # NOTE: business_model and marketing_plan have been moved to Phase 1 for quick decision-making
            phase1_doc_types = ["requirements", "project_charter", "user_stories", "business_model", "marketing_plan"]
            for doc_type in phase1_doc_types:
                if doc_type in results.get("status", {}):
                    if results["status"][doc_type] == "complete" or results["status"][doc_type] == "complete_v2":
                        all_successful_docs.append(doc_type)
                    elif results["status"][doc_type] == "failed":
                        all_failed_docs.append(doc_type)
            
            # Phase 2 documents (from phase2_summary)
            if "phase2_summary" in results:
                phase2_summary = results["phase2_summary"]
                for task in phase2_summary.get("successful", []):
                    all_successful_docs.append(task["doc_type"])
                for task in phase2_summary.get("failed", []):
                    all_failed_docs.append(task["doc_type"])
            
            # Phase 3 documents (quality_review, claude_cli_documentation, format_conversions, document_index)
            phase3_doc_types = ["quality_review", "claude_cli_documentation", "format_conversions", "document_index"]
            for doc_type in phase3_doc_types:
                if doc_type in results.get("status", {}):
                    status = results["status"][doc_type]
                    if status == "complete" or "partial" in status.lower():
                        all_successful_docs.append(doc_type)
                    elif status == "failed" or status == "skipped":
                        all_failed_docs.append(doc_type)
            
            # Log summary
            total_docs = len(all_successful_docs) + len(all_failed_docs)
            success_count = len(all_successful_docs)
            failed_count = len(all_failed_docs)
            
            logger.info(f"📈 Total Documents: {total_docs}")
            logger.info(f"✅ Successful: {success_count} ({success_count/total_docs*100:.1f}%)" if total_docs > 0 else "✅ Successful: 0")
            logger.info(f"❌ Failed: {failed_count} ({failed_count/total_docs*100:.1f}%)" if total_docs > 0 else "❌ Failed: 0")
            
            if all_successful_docs:
                logger.info(f"   ✅ Generated: {', '.join(sorted(set(all_successful_docs)))}")
            if all_failed_docs:
                logger.warning(f"   ❌ Failed: {', '.join(sorted(set(all_failed_docs)))}")
                # Log detailed error information for failed tasks
                if "phase2_summary" in results:
                    for failed_task in results["phase2_summary"].get("failed", []):
                        logger.warning(f"      - {failed_task['doc_type']}: {failed_task.get('error', 'Unknown error')}")
            
            logger.info("=" * 80)
            
            # Store final summary in results
            results["execution_summary"] = {
                "total_documents": total_docs,
                "successful_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count / total_docs * 100 if total_docs > 0 else 0,
                "successful_documents": sorted(set(all_successful_docs)),
                "failed_documents": sorted(set(all_failed_docs))
            }
            
            # --- PHASE 4: CODE ANALYSIS AND DOCUMENTATION UPDATE (Optional, Docs-First Mode Only) ---
            # Note: In code-first mode, code analysis was already done in Phase 0
            if workflow_mode == "docs_first" and codebase_path:
                logger.info("=" * 80)
                logger.info("--- PHASE 4: Code Analysis and Documentation Update (Docs-First Mode) ---")
                logger.info("=" * 80)
                logger.info(f"📁 Analyzing codebase at: {codebase_path}")
                
                try:
                    # Analyze codebase (I/O bound, run in executor)
                    logger.info("🔍 Step 1: Analyzing codebase structure...")
                    loop = asyncio.get_event_loop()
                    code_analysis = await loop.run_in_executor(
                        None,
                        lambda: self.code_analyst.analyze_codebase(codebase_path)
                    )
                    logger.info(f"  ✅ Code analysis complete: {len(code_analysis.get('modules', []))} modules, "
                              f"{len(code_analysis.get('classes', []))} classes, "
                              f"{len(code_analysis.get('functions', []))} functions")
                    
                    # Update API Documentation with code analysis (async I/O)
                    logger.info("📝 Step 2: Updating API documentation based on actual code...")
                    try:
                        # Get existing API documentation
                        api_doc_content = final_docs.get(AgentType.API_DOCUMENTATION)
                        
                        # Generate updated API documentation from code (async I/O)
                        updated_api_doc = await loop.run_in_executor(
                            None,
                            lambda: self.code_analyst.generate_code_documentation(
                                code_analysis=code_analysis,
                                existing_docs=api_doc_content
                            )
                        )
                        
                        # Save updated API documentation (async I/O)
                        api_doc_path = document_file_paths.get(AgentType.API_DOCUMENTATION)
                        if api_doc_path:
                            if Path(api_doc_path).is_absolute():
                                await loop.run_in_executor(
                                    None,
                                    lambda fp=api_doc_path, cnt=updated_api_doc: Path(fp).write_text(cnt, encoding='utf-8')
                                )
                            else:
                                await loop.run_in_executor(
                                    None,
                                    lambda fp=api_doc_path, cnt=updated_api_doc: self.file_manager.write_file(fp, cnt)
                                )
                            logger.info(f"  ✅ API documentation updated: {api_doc_path}")
                    except Exception as e:
                        logger.warning(f"  ⚠️  API documentation update failed: {e}")
                    
                    # Update Developer Documentation with code analysis (async I/O)
                    logger.info("📝 Step 3: Updating developer documentation based on actual code...")
                    try:
                        # Get existing developer documentation
                        dev_doc_content = final_docs.get(AgentType.DEVELOPER_DOCUMENTATION)
                        
                        # Generate updated developer documentation from code (async I/O)
                        updated_dev_doc = await loop.run_in_executor(
                            None,
                            lambda: self.code_analyst.generate_code_documentation(
                                code_analysis=code_analysis,
                                existing_docs=dev_doc_content
                            )
                        )
                        
                        # Save updated developer documentation (async I/O)
                        dev_doc_path = document_file_paths.get(AgentType.DEVELOPER_DOCUMENTATION)
                        if dev_doc_path:
                            if Path(dev_doc_path).is_absolute():
                                await loop.run_in_executor(
                                    None,
                                    lambda fp=dev_doc_path, cnt=updated_dev_doc: Path(fp).write_text(cnt, encoding='utf-8')
                                )
                            else:
                                await loop.run_in_executor(
                                    None,
                                    lambda fp=dev_doc_path, cnt=updated_dev_doc: self.file_manager.write_file(fp, cnt)
                                )
                            logger.info(f"  ✅ Developer documentation updated: {dev_doc_path}")
                    except Exception as e:
                        logger.warning(f"  ⚠️  Developer documentation update failed: {e}")
                    
                    # Save code analysis results (async I/O)
                    logger.info("💾 Step 4: Saving code analysis results...")
                    try:
                        import json
                        code_analysis_json = json.dumps(code_analysis, indent=2, default=str)
                        code_analysis_path = await loop.run_in_executor(
                            None,
                            lambda cnt=code_analysis_json: self.file_manager.write_file("code_analysis.json", cnt)
                        )
                        results["files"]["code_analysis"] = code_analysis_path
                        results["status"]["code_analysis"] = "complete"
                        logger.info(f"  ✅ Code analysis saved: {code_analysis_path}")
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to save code analysis: {e}")
                    
                    logger.info("=" * 80)
                    logger.info("✅ PHASE 4 COMPLETE: Code analysis and documentation update completed")
                    logger.info("=" * 80)
                    
                except Exception as e:
                    logger.error(f"  ❌ Phase 4 (Code Analysis) failed: {e}", exc_info=True)
                    results["status"]["code_analysis"] = "failed"
                    results["code_analysis_error"] = str(e)
            elif workflow_mode == "code_first":
                logger.debug("  Phase 4 skipped (code-first mode: code analysis was done in Phase 0)")
            else:
                logger.debug("  Phase 4 skipped (no codebase_path provided)")
            
            # Summary
            logger.info("=" * 80)
            logger.info(f"🚀 HYBRID Workflow COMPLETED (Async) for project {project_id}")
            logger.info("=" * 80)
            
            # Get documents summary (async I/O)
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                lambda: get_documents_summary(results["files"])
            )
            logger.info(f"Documents organized by level: Level 1: {len(summary['level_1_strategic']['documents'])}, "
                       f"Level 2: {len(summary['level_2_product']['documents'])}, "
                       f"Level 3: {len(summary['level_3_technical']['documents'])}, "
                       f"Cross-Level: {len(summary['cross_level']['documents'])}")
            
            results["documents_by_level"] = summary
            
            return results
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in HYBRID workflow (async): {str(e)}", exc_info=True)
            results["error"] = str(e)
            return results
    
    def get_workflow_status(self, project_id: str) -> Dict:
        """Get current workflow status for a project"""
        context = self.context_manager.get_shared_context(project_id)
        
        return {
            "project_id": project_id,
            "workflow_status": {
                agent_type.value: status.value
                for agent_type, status in context.workflow_status.items()
            },
            "completed_agents": [
                agent_type.value
                for agent_type, status in context.workflow_status.items()
                if status == DocumentStatus.COMPLETE
            ],
            "total_outputs": len(context.agent_outputs)
        }


"""
Marketing Plan Agent
Generates comprehensive marketing documentation including GTM strategy, target personas, channels, and launch plans
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_marketing_plan_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarketingPlanAgent(BaseAgent):
    """
    Marketing Plan Agent
    
    Generates marketing documentation including:
    - Go-to-Market (GTM) strategy
    - Target user personas (marketing-focused)
    - Competitive analysis
    - Value proposition and messaging
    - Marketing channels and tactics
    - Launch strategy and timeline
    """
    
    def __init__(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        rate_limiter: Optional[RequestQueue] = None,
        file_manager: Optional[FileManager] = None,
        api_key: Optional[str] = None,
        **provider_kwargs
    ):
        """Initialize Marketing Plan Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/marketing")
    
    def generate(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None,
        business_model_summary: Optional[str] = None
    ) -> str:
        """
        Generate marketing plan documentation
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            project_charter_summary: Optional Project Charter content
            business_model_summary: Optional Business Model content
        
        Returns:
            Generated marketing plan documentation (Markdown)
        """
        full_prompt = get_marketing_plan_prompt(
            requirements_summary,
            project_charter_summary,
            business_model_summary
        )
        
        try:
            marketing_doc = self._call_llm(full_prompt, temperature=0.7)
            logger.debug(f"Marketing Plan document generated (length: {len(marketing_doc)} characters)")
            return marketing_doc
        except Exception as e:
            logger.error(f"Error generating marketing plan: {e}")
            raise
    
    async def async_generate(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None,
        business_model_summary: Optional[str] = None
    ) -> str:
        """
        Generate marketing plan documentation (async)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            project_charter_summary: Optional Project Charter content
            business_model_summary: Optional Business Model content
        
        Returns:
            Generated marketing plan documentation (Markdown)
        """
        full_prompt = get_marketing_plan_prompt(
            requirements_summary,
            project_charter_summary,
            business_model_summary
        )
        
        try:
            marketing_doc = await self._async_call_llm(full_prompt, temperature=0.7)
            logger.debug(f"Marketing Plan document generated (async) (length: {len(marketing_doc)} characters)")
            return marketing_doc
        except Exception as e:
            logger.error(f"Error generating marketing plan (async): {e}")
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None,
        business_model_summary: Optional[str] = None,
        output_filename: str = "marketing_plan.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate marketing plan and save to file (sync version)
        
        Args:
            requirements_summary: Requirements summary
            project_charter_summary: Optional project charter
            business_model_summary: Optional business model
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        logger.info(f"Generating marketing plan for project: {project_id}")
        
        # Generate documentation
        marketing_doc = self.generate(
            requirements_summary,
            project_charter_summary,
            business_model_summary
        )
        
        # Save to file
        file_path = self.file_manager.write_file(output_filename, marketing_doc)
        logger.info(f"Marketing plan saved to: {file_path}")
        
        # Save to context if available
        if project_id and context_manager:
            try:
                output = AgentOutput(
                    agent_type=AgentType.MARKETING_PLAN,
                    document_type="marketing_plan",
                    content=marketing_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
                logger.debug("Marketing plan saved to context")
            except Exception as e:
                logger.warning(f"Could not save marketing plan to context: {e}")
        
        return file_path
    
    async def async_generate_and_save(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None,
        business_model_summary: Optional[str] = None,
        output_filename: str = "marketing_plan.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate marketing plan and save to file (async version)
        
        Args:
            requirements_summary: Requirements summary
            project_charter_summary: Optional project charter
            business_model_summary: Optional business model
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        import asyncio
        logger.info(f"Generating marketing plan (async) for project: {project_id}")
        
        # Generate documentation (async)
        marketing_doc = await self.async_generate(
            requirements_summary,
            project_charter_summary,
            business_model_summary
        )
        
        # Save to file (file I/O in executor)
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            lambda: self.file_manager.write_file(output_filename, marketing_doc)
        )
        logger.info(f"Marketing plan saved (async) to: {file_path}")
        
        # Save to context (async)
        if project_id and context_manager:
            output = AgentOutput(
                agent_type=AgentType.MARKETING_PLAN,
                document_type="marketing_plan",
                content=marketing_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE,
                generated_at=datetime.now()
            )
            await loop.run_in_executor(
                None,
                lambda: context_manager.save_agent_output(project_id, output)
            )
            logger.debug("Marketing plan saved to context (async)")
        
        return file_path


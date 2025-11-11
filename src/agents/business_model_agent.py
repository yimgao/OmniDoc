"""
Business Model Agent
Generates business model documentation including revenue models, pricing strategy, KPIs, and cost analysis
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_business_model_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BusinessModelAgent(BaseAgent):
    """
    Business Model Agent
    
    Generates business model documentation including:
    - Revenue models (SaaS, one-time, freemium, etc.)
    - Pricing strategy and tiers
    - Key Performance Indicators (KPIs)
    - Cost analysis and projections
    - Business metrics and success criteria
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
        """Initialize Business Model Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/business")
    
    def generate(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None
    ) -> str:
        """
        Generate business model documentation
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            project_charter_summary: Optional Project Charter content
        
        Returns:
            Generated business model documentation (Markdown)
        """
        full_prompt = get_business_model_prompt(requirements_summary, project_charter_summary)
        
        try:
            business_doc = self._call_llm(full_prompt, temperature=0.7)
            logger.debug(f"Business Model document generated (length: {len(business_doc)} characters)")
            return business_doc
        except Exception as e:
            logger.error(f"Error generating business model: {e}")
            raise
    
    async def async_generate(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None
    ) -> str:
        """
        Generate business model documentation (async)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            project_charter_summary: Optional Project Charter content
        
        Returns:
            Generated business model documentation (Markdown)
        """
        full_prompt = get_business_model_prompt(requirements_summary, project_charter_summary)
        
        try:
            business_doc = await self._async_call_llm(full_prompt, temperature=0.7)
            logger.debug(f"Business Model document generated (async) (length: {len(business_doc)} characters)")
            return business_doc
        except Exception as e:
            logger.error(f"Error generating business model (async): {e}")
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None,
        output_filename: str = "business_model.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate business model and save to file (sync version)
        
        Args:
            requirements_summary: Requirements summary
            project_charter_summary: Optional project charter
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        logger.info(f"Generating business model for project: {project_id}")
        
        # Generate documentation
        business_doc = self.generate(requirements_summary, project_charter_summary)
        
        # Save to file
        file_path = self.file_manager.write_file(output_filename, business_doc)
        logger.info(f"Business model saved to: {file_path}")
        
        # Save to context if available
        if project_id and context_manager:
            try:
                output = AgentOutput(
                    agent_type=AgentType.BUSINESS_MODEL,
                    document_type="business_model",
                    content=business_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
                logger.debug("Business model saved to context")
            except Exception as e:
                logger.warning(f"Could not save business model to context: {e}")
        
        return file_path
    
    async def async_generate_and_save(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None,
        output_filename: str = "business_model.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate business model and save to file (async version)
        
        Args:
            requirements_summary: Requirements summary
            project_charter_summary: Optional project charter
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        import asyncio
        logger.info(f"Generating business model (async) for project: {project_id}")
        
        # Generate documentation (async)
        business_doc = await self.async_generate(requirements_summary, project_charter_summary)
        
        # Save to file (file I/O in executor)
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            lambda: self.file_manager.write_file(output_filename, business_doc)
        )
        logger.info(f"Business model saved (async) to: {file_path}")
        
        # Save to context (async)
        if project_id and context_manager:
            output = AgentOutput(
                agent_type=AgentType.BUSINESS_MODEL,
                document_type="business_model",
                content=business_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE,
                generated_at=datetime.now()
            )
            await loop.run_in_executor(
                None,
                lambda: context_manager.save_agent_output(project_id, output)
            )
            logger.debug("Business model saved to context (async)")
        
        return file_path


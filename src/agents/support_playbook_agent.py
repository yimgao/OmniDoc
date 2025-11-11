"""
Support Playbook Agent
Generates customer support documentation including support channels, SLA, FAQ, and escalation paths
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_support_playbook_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SupportPlaybookAgent(BaseAgent):
    """
    Support Playbook Agent
    
    Generates customer support documentation including:
    - Support channels (email, chat, forum, etc.)
    - Service Level Agreements (SLA)
    - Internal FAQ for support team
    - Escalation paths and procedures
    - Common issues and solutions
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
        """Initialize Support Playbook Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/support")
    
    def generate(
        self,
        requirements_summary: dict,
        user_documentation_summary: Optional[str] = None
    ) -> str:
        """
        Generate support playbook documentation
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            user_documentation_summary: Optional User Documentation content
        
        Returns:
            Generated support playbook documentation (Markdown)
        """
        full_prompt = get_support_playbook_prompt(requirements_summary, user_documentation_summary)
        
        try:
            support_doc = self._call_llm(full_prompt, temperature=0.7)
            logger.debug(f"Support Playbook document generated (length: {len(support_doc)} characters)")
            return support_doc
        except Exception as e:
            logger.error(f"Error generating support playbook: {e}")
            raise
    
    async def async_generate(
        self,
        requirements_summary: dict,
        user_documentation_summary: Optional[str] = None
    ) -> str:
        """
        Generate support playbook documentation (async)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            user_documentation_summary: Optional User Documentation content
        
        Returns:
            Generated support playbook documentation (Markdown)
        """
        full_prompt = get_support_playbook_prompt(requirements_summary, user_documentation_summary)
        
        try:
            support_doc = await self._async_call_llm(full_prompt, temperature=0.7)
            logger.debug(f"Support Playbook document generated (async) (length: {len(support_doc)} characters)")
            return support_doc
        except Exception as e:
            logger.error(f"Error generating support playbook (async): {e}")
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        user_documentation_summary: Optional[str] = None,
        output_filename: str = "support_playbook.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate support playbook and save to file (sync version)
        
        Args:
            requirements_summary: Requirements summary
            user_documentation_summary: Optional user documentation
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        logger.info(f"Generating support playbook for project: {project_id}")
        
        # Generate documentation
        support_doc = self.generate(requirements_summary, user_documentation_summary)
        
        # Save to file
        file_path = self.file_manager.write_file(output_filename, support_doc)
        logger.info(f"Support playbook saved to: {file_path}")
        
        # Save to context if available
        if project_id and context_manager:
            try:
                output = AgentOutput(
                    agent_type=AgentType.SUPPORT_PLAYBOOK,
                    document_type="support_playbook",
                    content=support_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
                logger.debug("Support playbook saved to context")
            except Exception as e:
                logger.warning(f"Could not save support playbook to context: {e}")
        
        return file_path
    
    async def async_generate_and_save(
        self,
        requirements_summary: dict,
        user_documentation_summary: Optional[str] = None,
        output_filename: str = "support_playbook.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate support playbook and save to file (async version)
        
        Args:
            requirements_summary: Requirements summary
            user_documentation_summary: Optional user documentation
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        import asyncio
        logger.info(f"Generating support playbook (async) for project: {project_id}")
        
        # Generate documentation (async)
        support_doc = await self.async_generate(requirements_summary, user_documentation_summary)
        
        # Save to file (file I/O in executor)
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            lambda: self.file_manager.write_file(output_filename, support_doc)
        )
        logger.info(f"Support playbook saved (async) to: {file_path}")
        
        # Save to context (async)
        if project_id and context_manager:
            output = AgentOutput(
                agent_type=AgentType.SUPPORT_PLAYBOOK,
                document_type="support_playbook",
                content=support_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE,
                generated_at=datetime.now()
            )
            await loop.run_in_executor(
                None,
                lambda: context_manager.save_agent_output(project_id, output)
            )
            logger.debug("Support playbook saved to context (async)")
        
        return file_path


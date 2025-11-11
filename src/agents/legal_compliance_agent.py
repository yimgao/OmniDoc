"""
Legal & Compliance Agent
Generates legal and compliance documentation including privacy policy, terms of service, GDPR/CCPA compliance, and license checks
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_legal_compliance_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LegalComplianceAgent(BaseAgent):
    """
    Legal & Compliance Agent
    
    Generates legal and compliance documentation including:
    - Privacy Policy
    - Terms of Service
    - GDPR/CCPA compliance checklist
    - Data handling procedures
    - License compatibility check
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
        """Initialize Legal & Compliance Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/legal")
    
    def generate(
        self,
        requirements_summary: dict,
        technical_summary: Optional[str] = None
    ) -> str:
        """
        Generate legal and compliance documentation
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            technical_summary: Optional Technical Documentation content (for data handling info)
        
        Returns:
            Generated legal compliance documentation (Markdown)
        """
        full_prompt = get_legal_compliance_prompt(requirements_summary, technical_summary)
        
        try:
            legal_doc = self._call_llm(full_prompt, temperature=0.5)  # Lower temperature for legal accuracy
            logger.debug(f"Legal & Compliance document generated (length: {len(legal_doc)} characters)")
            return legal_doc
        except Exception as e:
            logger.error(f"Error generating legal compliance: {e}")
            raise
    
    async def async_generate(
        self,
        requirements_summary: dict,
        technical_summary: Optional[str] = None
    ) -> str:
        """
        Generate legal and compliance documentation (async)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            technical_summary: Optional Technical Documentation content
        
        Returns:
            Generated legal compliance documentation (Markdown)
        """
        full_prompt = get_legal_compliance_prompt(requirements_summary, technical_summary)
        
        try:
            legal_doc = await self._async_call_llm(full_prompt, temperature=0.5)
            logger.debug(f"Legal & Compliance document generated (async) (length: {len(legal_doc)} characters)")
            return legal_doc
        except Exception as e:
            logger.error(f"Error generating legal compliance (async): {e}")
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        technical_summary: Optional[str] = None,
        output_filename: str = "legal_compliance.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate legal compliance documentation and save to file (sync version)
        
        Args:
            requirements_summary: Requirements summary
            technical_summary: Optional technical documentation
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        logger.info(f"Generating legal compliance documentation for project: {project_id}")
        
        # Generate documentation
        legal_doc = self.generate(requirements_summary, technical_summary)
        
        # Save to file
        file_path = self.file_manager.write_file(output_filename, legal_doc)
        logger.info(f"Legal compliance documentation saved to: {file_path}")
        
        # Save to context if available
        if project_id and context_manager:
            try:
                output = AgentOutput(
                    agent_type=AgentType.LEGAL_COMPLIANCE,
                    document_type="legal_compliance",
                    content=legal_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
                logger.debug("Legal compliance documentation saved to context")
            except Exception as e:
                logger.warning(f"Could not save legal compliance to context: {e}")
        
        return file_path
    
    async def async_generate_and_save(
        self,
        requirements_summary: dict,
        technical_summary: Optional[str] = None,
        output_filename: str = "legal_compliance.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate legal compliance documentation and save to file (async version)
        
        Args:
            requirements_summary: Requirements summary
            technical_summary: Optional technical documentation
            output_filename: Output filename
            project_id: Project ID for context
            context_manager: Context manager instance
        
        Returns:
            Path to saved file
        """
        import asyncio
        logger.info(f"Generating legal compliance documentation (async) for project: {project_id}")
        
        # Generate documentation (async)
        legal_doc = await self.async_generate(requirements_summary, technical_summary)
        
        # Save to file (file I/O in executor)
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            lambda: self.file_manager.write_file(output_filename, legal_doc)
        )
        logger.info(f"Legal compliance documentation saved (async) to: {file_path}")
        
        # Save to context (async)
        if project_id and context_manager:
            output = AgentOutput(
                agent_type=AgentType.LEGAL_COMPLIANCE,
                document_type="legal_compliance",
                content=legal_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE,
                generated_at=datetime.now()
            )
            await loop.run_in_executor(
                None,
                lambda: context_manager.save_agent_output(project_id, output)
            )
            logger.debug("Legal compliance documentation saved to context (async)")
        
        return file_path


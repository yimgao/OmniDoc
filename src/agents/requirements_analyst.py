"""
Requirements Analyst Agent
Uses OOP structure with BaseAgent inheritance
"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.utils.requirements_parser import RequirementsParser
from src.rate_limit.queue_manager import RequestQueue
from src.context.context_manager import ContextManager
from src.context.shared_context import RequirementsDocument, AgentType, DocumentStatus, AgentOutput
from prompts.system_prompts import get_requirements_prompt
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RequirementsAnalyst(BaseAgent):
    """
    Requirements Analyst Agent
    
    Analyzes user ideas and generates structured requirements documents
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
        """
        Initialize Requirements Analyst
        
        Args:
            provider_name: LLM provider name ("gemini", "openai", etc.) - defaults to env var or "gemini"
            model_name: Model name override (provider-specific)
            rate_limiter: Shared rate limiter (optional)
            file_manager: File manager instance (optional)
            api_key: API key (optional, loads from env vars if not provided)
            **provider_kwargs: Additional provider-specific configuration
        
        Examples:
            >>> # Use default Gemini
            >>> agent = RequirementsAnalyst()
            
            >>> # Use OpenAI
            >>> agent = RequirementsAnalyst(provider_name="openai")
            
            >>> # Use specific GPT model
            >>> agent = RequirementsAnalyst(
            ...     provider_name="openai",
            ...     default_model="gpt-4o"
            ... )
        """
        # Initialize base agent with provider support
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        # Initialize file manager
        self.file_manager = file_manager or FileManager(base_dir="docs/requirements")

        # Initialize requirements parser
        self.parser = RequirementsParser()

        # Context manager (optional, will be set when project_id is provided)
        self.context_manager: Optional[ContextManager] = None
        self.project_id: Optional[str] = None
    
    def generate(self, user_idea: str) -> str:
        """
        Generate requirements document from user idea
        
        Args:
            user_idea: User's project idea/requirement
            
        Returns:
            Generated requirements document (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_requirements_prompt(user_idea)
        
        
        # Check rate limit stats
        stats = self.get_stats()
        
        try:
            requirements_doc = self._call_llm(full_prompt)
            logger.info("✅ Requirements document generated!")
            return requirements_doc
        except Exception as e:
            logger.error(f"Error generating requirements: {e}")
            raise
    
    def generate_and_save(
        self,
        user_idea: str,
        output_filename: str = "requirements.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate requirements and save to file
        
        Args:
            user_idea: User's project idea
            output_filename: Filename to save (will be saved in base_dir)
            project_id: Optional project ID for context sharing
            context_manager: Optional context manager for saving to shared context
            
        Returns:
            Absolute path to saved file
        """
        # Store context info if provided
        if project_id and context_manager:
            self.project_id = project_id
            self.context_manager = context_manager
        
        # Generate requirements
        logger.info(f"Starting requirements generation for: {output_filename}")
        requirements_doc = self.generate(user_idea)
        logger.debug(f"Requirements document generated (length: {len(requirements_doc)} characters)")
        
        # Save to database (not to file)
        try:
            # Generate virtual file path for reference (not used for actual file storage)
            virtual_path = f"docs/{output_filename}"
            logger.info(f"Requirements document saving to database (virtual path: {virtual_path})")
            
            # Save to context/database (with improved parsing)
            if self.project_id and self.context_manager:
                self._save_to_context(requirements_doc, virtual_path, user_idea)
                logger.info("✅ Requirements document saved to database")
            else:
                logger.warning("⚠️  No context manager available, document not saved to database")
            
            return virtual_path  # Return virtual path for compatibility
        except Exception as e:
            logger.error(f"Error saving requirements to database: {str(e)}", exc_info=True)
            logger.error("❌ Error saving to database: {{e}}")
            raise
    
    def _save_to_context(self, requirements_doc: str, file_path: str, user_idea: str):
        """Save requirements to shared context with intelligent parsing"""
        if not self.project_id or not self.context_manager:
            logger.debug("Skipping context save: project_id or context_manager not available")
            return

        try:
            logger.info(f"Saving requirements to context (project: {self.project_id})")
            # Create project if it doesn't exist
            self.context_manager.create_project(self.project_id, user_idea)

            # Parse requirements document intelligently
            req_doc = self.parser.parse_markdown(requirements_doc, user_idea)
            logger.debug(f"Requirements parsed: {len(req_doc.core_features)} features, "
                        f"{len(req_doc.user_personas)} personas, "
                        f"{len(req_doc.business_objectives)} objectives")

            # Save parsed requirements to context
            self.context_manager.save_requirements(self.project_id, req_doc)

            # Save agent output
            output = AgentOutput(
                agent_type=AgentType.REQUIREMENTS_ANALYST,
                document_type="requirements",
                content=requirements_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE
            )
            self.context_manager.save_agent_output(self.project_id, output)

            logger.info(f"Requirements saved to shared context (project: {self.project_id})")
            logger.debug(
                f"Extracted: {len(req_doc.core_features)} features, "
                  f"{len(req_doc.user_personas)} personas, "
                f"{len(req_doc.business_objectives)} objectives"
            )
        except Exception as e:
            logger.warning(f"Could not save to context: {str(e)}", exc_info=True)

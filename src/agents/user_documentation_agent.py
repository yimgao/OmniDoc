"""
User Documentation Agent
Generates end-user facing documentation and guides
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_user_prompt


class UserDocumentationAgent(BaseAgent):
    """
    User Documentation Agent
    
    Generates end-user documentation including:
    - Introduction and getting started
    - Installation & setup
    - Basic usage guides
    - Features guide
    - User interface guide
    - Common tasks tutorials
    - Troubleshooting
    - FAQ
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
        """Initialize User Documentation Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/user")
    
    def generate(self, requirements_summary: dict) -> str:
        """
        Generate user documentation from requirements
        
        Args:
            requirements_summary: Summary from Requirements Analyst
                Should contain: user_idea, project_overview, core_features, user_personas
        
        Returns:
            Generated user documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_user_prompt(requirements_summary)
        
        try:
            user_doc = self._call_llm(full_prompt)
            return user_doc
        except Exception as e:
            raise
    
    async def async_generate(self, requirements_summary: dict) -> str:
        """
        Generate user documentation from requirements (async)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
        
        Returns:
            Generated user documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_user_prompt(requirements_summary)
        
        try:
            user_doc = await self._async_call_llm(full_prompt)
            return user_doc
        except Exception as e:
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        output_filename: str = "user_guide.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate user documentation and save to file (sync version)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
            
        Returns:
            Absolute path to saved file
        """
        # Generate documentation
        user_doc = self.generate(requirements_summary)
        
        # Save to file
        try:
            file_path = self.file_manager.write_file(output_filename, user_doc)
            file_size = self.file_manager.get_file_size(output_filename)
            
            # Save to context if available
            if project_id and context_manager:
                output = AgentOutput(
                    agent_type=AgentType.USER_DOCUMENTATION,
                    document_type="user_guide",
                    content=user_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
            
            return file_path
        except Exception as e:
            raise
    
    async def async_generate_and_save(
        self,
        requirements_summary: dict,
        output_filename: str = "user_guide.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate user documentation and save to file (async version)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
            
        Returns:
            Absolute path to saved file
        """
        import asyncio
        # Generate documentation (async)
        user_doc = await self.async_generate(requirements_summary)
        
        # Save to file (file I/O in executor)
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            lambda: self.file_manager.write_file(output_filename, user_doc)
        )
        
        # Save to context (async)
        if project_id and context_manager:
            output = AgentOutput(
                agent_type=AgentType.USER_DOCUMENTATION,
                document_type="user_guide",
                content=user_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE,
                generated_at=datetime.now()
            )
            await loop.run_in_executor(
                None,
                lambda: context_manager.save_agent_output(project_id, output)
            )
        
        return file_path


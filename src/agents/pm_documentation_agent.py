"""
Project Manager Documentation Agent
Generates project management documentation (timeline, resources, risks, milestones)
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_pm_prompt


class PMDocumentationAgent(BaseAgent):
    """
    Project Manager Documentation Agent
    
    Generates project management documentation including:
    - Project timeline and milestones
    - Resource requirements
    - Risk assessment
    - Budget estimation
    - Team structure
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
        """Initialize PM Documentation Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/pm")
    
    def generate(self, requirements_summary: dict, project_charter_summary: Optional[str] = None) -> str:
        """
        Generate PM documentation from requirements and project charter
        
        Args:
            requirements_summary: Summary from Requirements Analyst
                Should contain: user_idea, project_overview, core_features, technical_requirements
            project_charter_summary: Optional Project Charter content (Level 1 output)
        
        Returns:
            Generated PM documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_pm_prompt(requirements_summary, project_charter_summary)
        
        try:
            pm_doc = self._call_llm(full_prompt)
            return pm_doc
        except Exception as e:
            raise
    
    async def async_generate(self, requirements_summary: dict, project_charter_summary: Optional[str] = None) -> str:
        """
        Generate PM documentation from requirements and project charter (async)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            project_charter_summary: Optional Project Charter content
        
        Returns:
            Generated PM documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_pm_prompt(requirements_summary, project_charter_summary)
        
        try:
            pm_doc = await self._async_call_llm(full_prompt)
            return pm_doc
        except Exception as e:
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        project_charter_summary: Optional[str] = None,
        output_filename: str = "project_plan.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate PM documentation and save to file (sync version)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            project_charter_summary: Optional Project Charter content
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
            
        Returns:
            Absolute path to saved file
        """
        # Generate documentation
        pm_doc = self.generate(requirements_summary, project_charter_summary)
        
        # Save to file
        try:
            file_path = self.file_manager.write_file(output_filename, pm_doc)
            file_size = self.file_manager.get_file_size(output_filename)
            
            # Save to context if available
            if project_id and context_manager:
                output = AgentOutput(
                    agent_type=AgentType.PM_DOCUMENTATION,
                    document_type="project_plan",
                    content=pm_doc,
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
        project_charter_summary: Optional[str] = None,
        output_filename: str = "project_plan.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate PM documentation and save to file (async version)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            project_charter_summary: Optional Project Charter content
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
            
        Returns:
            Absolute path to saved file
        """
        import asyncio
        # Generate documentation (async)
        pm_doc = await self.async_generate(requirements_summary, project_charter_summary)
        
        # Save to file (file I/O in executor)
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            lambda: self.file_manager.write_file(output_filename, pm_doc)
        )
        
        # Save to context (async)
        if project_id and context_manager:
            output = AgentOutput(
                agent_type=AgentType.PM_DOCUMENTATION,
                document_type="project_plan",
                content=pm_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE,
                generated_at=datetime.now()
            )
            await loop.run_in_executor(
                None,
                lambda: context_manager.save_agent_output(project_id, output)
            )
        
        return file_path


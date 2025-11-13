"""
Test Documentation Agent
Generates comprehensive test documentation (test plans, test cases, QA strategies)
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_test_prompt


class TestDocumentationAgent(BaseAgent):
    """
    Test Documentation Agent
    
    Generates test documentation including:
    - Test strategy and methodology
    - Test plan with scope and schedule
    - Detailed test cases
    - Test scenarios (E2E, integration)
    - Regression testing strategy
    - Performance testing plans
    - Security testing cases
    - Test environment setup
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
        """Initialize Test Documentation Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/test")
    
    def generate(
        self,
        requirements_summary: dict,
        technical_summary: Optional[str] = None,
        api_summary: Optional[str] = None,
        database_schema_summary: Optional[str] = None,
        user_stories_summary: Optional[str] = None
    ) -> str:
        """
        Generate test documentation from requirements and technical specs
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            technical_summary: Optional technical documentation summary
            api_summary: Optional API documentation summary - used to design API endpoint test cases
            database_schema_summary: Optional database schema summary - used to design database operation test cases
            user_stories_summary: Optional user stories summary - used to design user story test cases
        
        Returns:
            Generated test documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_test_prompt(
            requirements_summary, 
            technical_summary,
            api_summary=api_summary,
            database_schema_summary=database_schema_summary,
            user_stories_summary=user_stories_summary
        )
        
        try:
            test_doc = self._call_llm(full_prompt)
            return test_doc
        except Exception as e:
            raise
    
    async def async_generate(
        self,
        requirements_summary: dict,
        technical_summary: Optional[str] = None,
        api_summary: Optional[str] = None,
        database_schema_summary: Optional[str] = None,
        user_stories_summary: Optional[str] = None
    ) -> str:
        """
        Generate test documentation from requirements and technical specs (async)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            technical_summary: Optional technical documentation summary
            api_summary: Optional API documentation summary - used to design API endpoint test cases
            database_schema_summary: Optional database schema summary - used to design database operation test cases
            user_stories_summary: Optional user stories summary - used to design user story test cases
        
        Returns:
            Generated test documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_test_prompt(
            requirements_summary, 
            technical_summary,
            api_summary=api_summary,
            database_schema_summary=database_schema_summary,
            user_stories_summary=user_stories_summary
        )
        
        try:
            test_doc = await self._async_call_llm(full_prompt)
            return test_doc
        except Exception as e:
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        technical_summary: Optional[str] = None,
        api_summary: Optional[str] = None,
        database_schema_summary: Optional[str] = None,
        user_stories_summary: Optional[str] = None,
        output_filename: str = "test_plan.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None,
        **kwargs
    ) -> str:
        """
        Generate test documentation and save to file (sync version)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            technical_summary: Optional technical documentation summary
            api_summary: Optional API documentation summary - used to design API endpoint test cases
            database_schema_summary: Optional database schema summary - used to design database operation test cases
            user_stories_summary: Optional user stories summary - used to design user story test cases
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
        
        Returns:
            Absolute path to saved file
        """
        # Extract from kwargs if not provided directly
        if api_summary is None:
            api_summary = kwargs.get("api_summary")
        if database_schema_summary is None:
            database_schema_summary = kwargs.get("database_schema_summary")
        if user_stories_summary is None:
            user_stories_summary = kwargs.get("user_stories_summary")
        
        # Generate documentation
        test_doc = self.generate(
            requirements_summary, 
            technical_summary,
            api_summary=api_summary,
            database_schema_summary=database_schema_summary,
            user_stories_summary=user_stories_summary
        )
        
        # Save to file
        try:
            file_path = self.file_manager.write_file(output_filename, test_doc)
            file_size = self.file_manager.get_file_size(output_filename)
            
            # Save to context if available
            if project_id and context_manager:
                output = AgentOutput(
                    agent_type=AgentType.TEST_DOCUMENTATION,
                    document_type="test_plan",
                    content=test_doc,
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
        technical_summary: Optional[str] = None,
        api_summary: Optional[str] = None,
        database_schema_summary: Optional[str] = None,
        user_stories_summary: Optional[str] = None,
        output_filename: str = "test_plan.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None,
        **kwargs
    ) -> str:
        """
        Generate test documentation and save to file (async version)
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            technical_summary: Optional technical documentation summary
            api_summary: Optional API documentation summary - used to design API endpoint test cases
            database_schema_summary: Optional database schema summary - used to design database operation test cases
            user_stories_summary: Optional user stories summary - used to design user story test cases
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
        
        Returns:
            Absolute path to saved file
        """
        import asyncio
        # Extract from kwargs if not provided directly
        if api_summary is None:
            api_summary = kwargs.get("api_summary")
        if database_schema_summary is None:
            database_schema_summary = kwargs.get("database_schema_summary")
        if user_stories_summary is None:
            user_stories_summary = kwargs.get("user_stories_summary")
        
        # Generate documentation (async)
        test_doc = await self.async_generate(
            requirements_summary, 
            technical_summary,
            api_summary=api_summary,
            database_schema_summary=database_schema_summary,
            user_stories_summary=user_stories_summary
        )
        
        # Save to file (file I/O in executor)
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            lambda: self.file_manager.write_file(output_filename, test_doc)
        )
        
        # Save to context (async)
        if project_id and context_manager:
            output = AgentOutput(
                agent_type=AgentType.TEST_DOCUMENTATION,
                document_type="test_plan",
                content=test_doc,
                file_path=file_path,
                status=DocumentStatus.COMPLETE,
                generated_at=datetime.now()
            )
            await loop.run_in_executor(
                None,
                lambda: context_manager.save_agent_output(project_id, output)
            )
        
        return file_path


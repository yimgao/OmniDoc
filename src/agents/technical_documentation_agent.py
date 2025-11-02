"""
Technical Documentation Agent
Generates technical specifications and architecture documentation
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_technical_prompt


class TechnicalDocumentationAgent(BaseAgent):
    """
    Technical Documentation Agent
    
    Generates technical documentation including:
    - System architecture
    - Technical stack recommendations
    - Database design
    - API design
    - Security considerations
    - Deployment architecture
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
        """Initialize Technical Documentation Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/technical")
    
    def generate(self, requirements_summary: dict) -> str:
        """
        Generate technical documentation from requirements
        
        Args:
            requirements_summary: Summary from Requirements Analyst
                Should contain: user_idea, project_overview, core_features, technical_requirements
        
        Returns:
            Generated technical documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_technical_prompt(requirements_summary)
        
        print(f"🤖 {self.agent_name} is generating technical documentation...")
        print("⏳ This may take a moment (rate limited)...")
        
        stats = self.get_stats()
        print(f"📊 Rate limit status: {stats['requests_in_window']}/{stats['max_rate']} requests in window")
        
        try:
            technical_doc = self._call_llm(full_prompt)
            print("✅ Technical documentation generated!")
            return technical_doc
        except Exception as e:
            print(f"❌ Error generating technical documentation: {e}")
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        output_filename: str = "technical_spec.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate technical documentation and save to file
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
            
        Returns:
            Absolute path to saved file
        """
        # Generate documentation
        technical_doc = self.generate(requirements_summary)
        
        # Save to file
        try:
            file_path = self.file_manager.write_file(output_filename, technical_doc)
            file_size = self.file_manager.get_file_size(output_filename)
            print(f"✅ File written successfully to {file_path}")
            print(f"📄 File saved: {output_filename} ({file_size} bytes)")
            
            # Save to context if available
            if project_id and context_manager:
                output = AgentOutput(
                    agent_type=AgentType.TECHNICAL_DOCUMENTATION,
                    document_type="technical_spec",
                    content=technical_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now(),
                    dependencies=["requirements"]  # Depends on requirements
                )
                context_manager.save_agent_output(project_id, output)
                print(f"✅ Technical documentation saved to shared context (project: {project_id})")
            
            return file_path
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            raise


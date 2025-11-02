"""
Stakeholder Communication Agent
Generates business-focused documentation for non-technical stakeholders
"""
from typing import Optional
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_stakeholder_prompt


class StakeholderCommunicationAgent(BaseAgent):
    """
    Stakeholder Communication Agent
    
    Generates stakeholder documentation including:
    - Executive summary
    - Business objectives
    - Project scope
    - Timeline and milestones
    - Resource requirements
    - Risk assessment
    - Expected benefits
    - Next steps
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
        """Initialize Stakeholder Communication Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/stakeholder")
    
    def generate(
        self,
        requirements_summary: dict,
        pm_summary: Optional[str] = None
    ) -> str:
        """
        Generate stakeholder documentation from requirements and PM docs
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            pm_summary: Optional PM documentation summary
        
        Returns:
            Generated stakeholder documentation (Markdown)
        """
        # Get prompt from centralized prompts config
        full_prompt = get_stakeholder_prompt(requirements_summary, pm_summary)
        
        print(f"🤖 {self.agent_name} is generating stakeholder documentation...")
        print("⏳ This may take a moment (rate limited)...")
        
        stats = self.get_stats()
        print(f"📊 Rate limit status: {stats['requests_in_window']}/{stats['max_rate']} requests in window")
        
        try:
            stakeholder_doc = self._call_llm(full_prompt)
            print("✅ Stakeholder documentation generated!")
            return stakeholder_doc
        except Exception as e:
            print(f"❌ Error generating stakeholder documentation: {e}")
            raise
    
    def generate_and_save(
        self,
        requirements_summary: dict,
        pm_summary: Optional[str] = None,
        output_filename: str = "stakeholder_summary.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate stakeholder documentation and save to file
        
        Args:
            requirements_summary: Summary from Requirements Analyst
            pm_summary: Optional PM documentation summary
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
            
        Returns:
            Absolute path to saved file
        """
        # Generate documentation
        stakeholder_doc = self.generate(requirements_summary, pm_summary)
        
        # Save to file
        try:
            file_path = self.file_manager.write_file(output_filename, stakeholder_doc)
            file_size = self.file_manager.get_file_size(output_filename)
            print(f"✅ File written successfully to {file_path}")
            print(f"📄 File saved: {output_filename} ({file_size} bytes)")
            
            # Save to context if available
            if project_id and context_manager:
                output = AgentOutput(
                    agent_type=AgentType.STAKEHOLDER_COMMUNICATION,
                    document_type="stakeholder_summary",
                    content=stakeholder_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
                print(f"✅ Stakeholder documentation saved to shared context (project: {project_id})")
            
            return file_path
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            raise


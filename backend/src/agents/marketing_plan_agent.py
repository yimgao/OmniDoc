"""
Marketing Plan Agent
Specialized agent for generating marketing plans and GTM strategies
"""
from typing import Optional, Dict
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_marketing_plan_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarketingPlanAgent(BaseAgent):
    """
    Marketing Plan Agent
    
    Generates comprehensive marketing plans and Go-to-Market (GTM) strategies
    using expert prompts that ensure all required sections are included.
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
        Initialize Marketing Plan Agent
        
        Args:
            provider_name: LLM provider name ("gemini", "openai", etc.)
            model_name: Model name override (provider-specific)
            rate_limiter: Shared rate limiter (optional)
            file_manager: File manager instance (optional)
            api_key: API key (optional, loads from env vars if not provided)
            **provider_kwargs: Additional provider-specific configuration
        """
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
        user_idea: str,
        requirements_summary: Optional[Dict] = None,
        project_charter_summary: Optional[str] = None,
        business_model_summary: Optional[str] = None,
        dependency_documents: Optional[Dict[str, Dict[str, str]]] = None
    ) -> str:
        """
        Generate marketing plan document
        
        Args:
            user_idea: User's project idea
            requirements_summary: Requirements summary dict (optional)
            project_charter_summary: Project charter content (optional)
            business_model_summary: Business model content (optional)
            dependency_documents: Dependency documents dict (optional)
            
        Returns:
            Generated marketing plan document (Markdown)
        """
        # Build requirements summary if not provided
        if not requirements_summary:
            requirements_summary = {"user_idea": user_idea}
        
        # Extract dependency documents if provided
        if dependency_documents:
            if not project_charter_summary and "project_charter" in dependency_documents:
                project_charter_summary = dependency_documents["project_charter"].get("content", "")
            if not business_model_summary and "business_model" in dependency_documents:
                business_model_summary = dependency_documents["business_model"].get("content", "")
            if not business_model_summary and "feature_roadmap" in dependency_documents:
                # Feature roadmap can also inform marketing plan
                feature_roadmap = dependency_documents["feature_roadmap"].get("content", "")
                if feature_roadmap and not project_charter_summary:
                    project_charter_summary = feature_roadmap[:2000]  # Use as context
        
        # Get expert prompt
        full_prompt = get_marketing_plan_prompt(
            requirements_summary=requirements_summary,
            project_charter_summary=project_charter_summary,
            business_model_summary=business_model_summary
        )
        
        try:
            marketing_plan = self._call_llm(full_prompt)
            logger.info("✅ Marketing plan generated!")
            return marketing_plan
        except Exception as e:
            logger.error(f"Error generating marketing plan: {e}")
            raise


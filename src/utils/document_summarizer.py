"""
Document Summarizer Utility
Replaces truncation with intelligent LLM-based summarization
"""
from typing import Optional
from src.llm.base_provider import BaseLLMProvider
from src.llm.provider_factory import ProviderFactory
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


class DocumentSummarizer:
    """
    Summarizes documents using LLM instead of simple truncation.
    This ensures downstream agents receive complete, semantic summaries
    rather than cut-off text.
    """
    
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        provider_name: Optional[str] = None,
        max_summary_length: int = 2000
    ):
        """
        Initialize document summarizer
        
        Args:
            llm_provider: Pre-configured LLM provider (if None, creates from provider_name)
            provider_name: Name of provider ("gemini", "openai", etc.)
            max_summary_length: Target maximum length for summaries in characters
        """
        settings = get_settings()
        self.llm_provider = llm_provider or ProviderFactory.create_provider(
            provider_name or settings.default_llm_provider
        )
        self.max_summary_length = max_summary_length
        logger.info(f"DocumentSummarizer initialized (max_length: {max_summary_length})")
    
    def summarize(
        self,
        document_content: str,
        document_type: str = "document",
        focus_areas: Optional[list] = None,
        max_length: Optional[int] = None
    ) -> str:
        """
        Summarize a document using LLM
        
        Args:
            document_content: Full document content to summarize
            document_type: Type of document (e.g., "technical documentation", "API documentation")
            focus_areas: Optional list of areas to focus on in summary
            max_length: Override default max_summary_length
        
        Returns:
            Summarized document content
        """
        target_length = max_length or self.max_summary_length
        
        # If document is already short enough, return as-is
        if len(document_content) <= target_length:
            logger.debug(f"Document already short enough ({len(document_content)} chars), returning as-is")
            return document_content
        
        # Build summarization prompt
        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nFocus on these areas:\n" + "\n".join(f"- {area}" for area in focus_areas)
        
        prompt = f"""You are a technical documentation summarizer. Your task is to create a comprehensive, complete summary of the following {document_type}.

CRITICAL REQUIREMENTS:
1. Create a COMPLETE summary - do not cut off mid-sentence or mid-thought
2. Preserve all key technical details, API endpoints, database schemas, and architectural decisions
3. Maintain the logical structure and flow of the original document
4. Keep all important specifications, requirements, and design decisions
5. The summary should be approximately {target_length} characters or less
6. Ensure the summary is semantically complete - it should read as a finished document, not a truncated one
{focus_text}

Now, summarize the following {document_type}:

{document_content}"""
        
        try:
            logger.debug(f"Summarizing {document_type} ({len(document_content)} chars -> target: {target_length} chars)")
            summary = self.llm_provider.generate(prompt, temperature=0.3)  # Lower temperature for more consistent summaries
            
            # Clean the response
            summary = summary.strip()
            
            # Remove markdown code blocks if present
            if summary.startswith("```"):
                lines = summary.split("\n")
                if len(lines) > 2:
                    summary = "\n".join(lines[1:-1])
            
            logger.debug(f"Summary generated ({len(summary)} chars)")
            return summary
            
        except Exception as e:
            logger.warning(f"Summarization failed: {e}, falling back to truncation")
            # Fallback to smart truncation (at sentence boundary)
            return self._smart_truncate(document_content, target_length)
    
    def summarize_for_agent(
        self,
        document_content: str,
        target_agent: str,
        document_type: str = "document"
    ) -> str:
        """
        Summarize a document with focus areas specific to the target agent
        
        Args:
            document_content: Full document content to summarize
            target_agent: Name of agent that will receive the summary
            document_type: Type of document being summarized
        
        Returns:
            Summarized document content optimized for the target agent
        """
        # Define focus areas for different agents
        agent_focus_areas = {
            "api_documentation": {
                "technical_documentation": [
                    "API endpoints and routes",
                    "Database schema and data models",
                    "Authentication mechanisms",
                    "Error handling patterns",
                    "System architecture"
                ],
                "user_stories": [
                    "User workflows and use cases",
                    "Feature requirements",
                    "User interactions"
                ]
            },
            "developer_documentation": {
                "technical_documentation": [
                    "Technology stack",
                    "System architecture",
                    "Code structure",
                    "Development setup requirements",
                    "Dependencies"
                ],
                "api_documentation": [
                    "API endpoints",
                    "Request/response formats",
                    "Authentication",
                    "Code examples"
                ]
            },
            "test_documentation": {
                "technical_documentation": [
                    "API endpoints to test",
                    "Database operations",
                    "System components",
                    "Architecture for integration tests"
                ]
            },
            "quality_reviewer": {
                "all": [
                    "Complete sections and content",
                    "Technical accuracy",
                    "Consistency",
                    "Completeness"
                ]
            }
        }
        
        # Get focus areas for this agent and document type
        focus_areas = None
        if target_agent in agent_focus_areas:
            agent_config = agent_focus_areas[target_agent]
            if document_type in agent_config:
                focus_areas = agent_config[document_type]
            elif "all" in agent_config:
                focus_areas = agent_config["all"]
        
        return self.summarize(document_content, document_type, focus_areas)
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        Fallback: Smart truncation at sentence boundary
        
        Args:
            text: Text to truncate
            max_length: Maximum length
        
        Returns:
            Truncated text ending at sentence boundary
        """
        if len(text) <= max_length:
            return text
        
        # Try to truncate at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind(".")
        last_newline = truncated.rfind("\n")
        
        # Use the later of period or newline
        cut_point = max(last_period, last_newline)
        
        if cut_point > max_length * 0.8:  # Only if we're keeping at least 80% of target length
            return truncated[:cut_point + 1] + "..."
        else:
            return truncated + "..."


# Global instance for easy access
_summarizer_instance: Optional[DocumentSummarizer] = None


def get_summarizer() -> DocumentSummarizer:
    """Get or create global summarizer instance"""
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = DocumentSummarizer()
    return _summarizer_instance


def summarize_document(
    document_content: str,
    document_type: str = "document",
    target_agent: Optional[str] = None,
    focus_areas: Optional[list] = None
) -> str:
    """
    Convenience function to summarize a document
    
    Args:
        document_content: Document content to summarize
        document_type: Type of document
        target_agent: Optional target agent name for agent-specific summarization
        focus_areas: Optional list of focus areas
    
    Returns:
        Summarized document
    """
    summarizer = get_summarizer()
    
    if target_agent:
        return summarizer.summarize_for_agent(document_content, target_agent, document_type)
    else:
        return summarizer.summarize(document_content, document_type, focus_areas)


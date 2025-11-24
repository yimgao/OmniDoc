"""
Document Improver Agent
Automatically improves documents based on quality review feedback
"""
from typing import Optional, Dict
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentImproverAgent(BaseAgent):
    """
    Document Improver Agent
    
    Automatically improves documents based on quality review feedback.
    This agent takes the original document and quality review suggestions,
    then generates an improved version.
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
        """Initialize Document Improver Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager()
    
    def generate(self, input_data: str) -> str:
        """
        Generate improved document (required by BaseAgent)
        
        Args:
            input_data: JSON string with 'original_document', 'document_type', 'quality_feedback'
        
        Returns:
            Improved document content
        """
        import json
        try:
            data = json.loads(input_data)
            return self.improve_document(
                original_document=data.get('original_document', ''),
                document_type=data.get('document_type', 'document'),
                quality_feedback=data.get('quality_feedback', ''),
                focus_areas=data.get('focus_areas')
            )
        except (json.JSONDecodeError, KeyError):
            # Fallback: treat input_data as quality feedback for a simple document
            return self.improve_document(
                original_document="",
                document_type="document",
                quality_feedback=input_data
            )
    
    def improve_document(
        self,
        original_document: str,
        document_type: str,
        quality_feedback: str,
        focus_areas: Optional[list] = None,
        quality_score: Optional[float] = None,
        quality_details: Optional[Dict] = None,
        structured_feedback: Optional[Dict] = None
    ) -> str:
        """
        Improve a document based on quality review feedback
        
        Args:
            original_document: The original document content
            document_type: Type of document (e.g., "technical_documentation")
            quality_feedback: Quality review feedback and suggestions
            focus_areas: Optional list of specific areas to focus on
            quality_score: Optional current quality score (0-100)
            quality_details: Optional quality check details (word_count, sections, readability)
            structured_feedback: Optional structured JSON feedback from LLM-as-Judge
                               (dict with score, feedback, suggestion, missing_sections, etc.)
        
        Returns:
            Improved document content
        """
        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nFocus on these specific areas:\n" + "\n".join(f"- {area}" for area in focus_areas)
        
        # Build quality score context
        score_context = ""
        if quality_score is not None:
            score_context = f"\n\nCURRENT QUALITY SCORE: {quality_score:.2f}/100\n"
            if quality_details:
                word_count_info = quality_details.get("word_count", {})
                sections_info = quality_details.get("sections", {})
                readability_info = quality_details.get("readability", {})
                
                score_context += "\nQUALITY METRICS:\n"
                score_context += f"- Word Count: {word_count_info.get('word_count', 0)} (min: {word_count_info.get('min_threshold', 100)}, passed: {word_count_info.get('passed', False)})\n"
                score_context += f"- Section Completeness: {sections_info.get('completeness_score', 0):.1f}% ({sections_info.get('found_count', 0)}/{sections_info.get('required_count', 0)} sections found)\n"
                if sections_info.get('missing_sections'):
                    missing = sections_info.get('missing_sections', [])[:5]  # Limit to 5
                    missing_clean = [s.replace('^#+\\s+', '').replace('\\s+', ' ') for s in missing]
                    score_context += f"  - MISSING SECTIONS: {', '.join(missing_clean)}\n"
                score_context += f"- Readability: {readability_info.get('readability_score', 0):.1f} ({readability_info.get('level', 'unknown')}, passed: {readability_info.get('passed', False)})\n"
                
                score_context += "\nCRITICAL IMPROVEMENT PRIORITIES:\n"
                if not word_count_info.get('passed', False):
                    score_context += f"1. INCREASE WORD COUNT: Current {word_count_info.get('word_count', 0)} words, need at least {word_count_info.get('min_threshold', 100)} words\n"
                    score_context += "   - Expand existing sections with more detail\n"
                    score_context += "   - Add examples, explanations, and context\n"
                    score_context += "   - Include more comprehensive coverage of topics\n"
                
                if not sections_info.get('passed', False) or sections_info.get('completeness_score', 100) < 80:
                    score_context += f"2. ADD MISSING SECTIONS: Only {sections_info.get('found_count', 0)}/{sections_info.get('required_count', 0)} sections found\n"
                    if sections_info.get('missing_sections'):
                        missing = sections_info.get('missing_sections', [])[:5]
                        missing_clean = [s.replace('^#+\\s+', '').replace('\\s+', ' ') for s in missing]
                        score_context += f"   - MUST ADD: {', '.join(missing_clean)}\n"
                    score_context += "   - Ensure all required sections are present with substantial content\n"
                
                if not readability_info.get('passed', False):
                    score_context += f"3. IMPROVE READABILITY: Current score {readability_info.get('readability_score', 0):.1f}, need at least {readability_info.get('min_threshold', 50):.1f}\n"
                    score_context += "   - Use simpler sentence structures\n"
                    score_context += "   - Break up long paragraphs\n"
                    score_context += "   - Use clearer, more direct language\n"
                    score_context += "   - Add more examples and explanations\n"
        
        # Build structured feedback context if available (LLM-as-Judge)
        structured_context = ""
        if structured_feedback:
            structured_context = "\n\n## STRUCTURED QUALITY FEEDBACK (LLM-as-Judge):\n"
            structured_context += f"**Quality Score: {structured_feedback.get('score', 5.0):.1f}/10**\n\n"
            structured_context += f"**Overall Feedback:** {structured_feedback.get('feedback', 'No feedback')}\n\n"
            structured_context += f"**Primary Suggestion:** {structured_feedback.get('suggestion', 'No specific suggestion')}\n\n"
            
            if structured_feedback.get('missing_sections'):
                structured_context += f"**Missing Sections (MUST ADD):** {', '.join(structured_feedback['missing_sections'])}\n\n"
            
            if structured_feedback.get('strengths'):
                structured_context += f"**Strengths:**\n"
                for strength in structured_feedback['strengths']:
                    structured_context += f"- {strength}\n"
                structured_context += "\n"
            
            if structured_feedback.get('weaknesses'):
                structured_context += f"**Weaknesses (MUST ADDRESS):**\n"
                for weakness in structured_feedback['weaknesses']:
                    structured_context += f"- {weakness}\n"
                structured_context += "\n"
            
            if structured_feedback.get('readability_issues'):
                structured_context += f"**Readability Issues:**\n"
                for issue in structured_feedback['readability_issues']:
                    structured_context += f"- {issue}\n"
                structured_context += "\n"
            
            if structured_feedback.get('priority_improvements'):
                structured_context += f"**Priority Improvements (HIGH PRIORITY):**\n"
                for improvement in structured_feedback['priority_improvements'][:5]:  # Limit to top 5
                    if isinstance(improvement, dict):
                        structured_context += f"- **{improvement.get('area', 'Unknown')}**: {improvement.get('issue', '')}\n"
                        structured_context += f"  → Suggestion: {improvement.get('suggestion', '')}\n"
                structured_context += "\n"
            
            structured_context += "**CRITICAL:** Address ALL items in the structured feedback above. Focus on the priority improvements first.\n"
        
        # Calculate original document length for reference
        original_length = len(original_document)
        
        prompt = f"""You are a Documentation Improvement Specialist. Your task is to improve a document by ADDING information based on quality review feedback, while preserving the existing content and structure.

CRITICAL INSTRUCTIONS:
1. Read the original document carefully and preserve ALL existing content
2. Review the quality feedback and improvement suggestions
3. Analyze the quality metrics to understand what needs to be added
4. ADD new information to address the issues, while keeping the original structure
5. The improved document MUST:
   - PRESERVE all existing sections and content (do not remove or rewrite)
   - ADD missing sections with substantial, high-quality content
   - EXPAND existing sections by adding more detail, examples, and explanations
   - IMPROVE readability by adding clarifications (but keep original text)
   - ADDRESS all specific issues mentioned in the feedback by adding content
   - MAINTAIN the original document structure and formatting
6. Focus on ADDITIVE improvements - add information, don't rewrite
7. If sections are missing, ADD them with detailed, high-quality content
8. If word count is low, EXPAND existing sections by adding more detail, examples, and explanations
9. If readability needs improvement, ADD clarifications and examples without changing existing text

🚨 CRITICAL LENGTH REQUIREMENT:
- The improved document MUST be LONGER than the original (unless original was extremely long, >100k chars)
- Original document length: {original_length:,} characters
- If the improved document is shorter, it means you deleted content, which is NOT allowed
- You MUST ADD content, not remove it
- The improved document should be at least 10-20% longer than the original to show improvement

🚨 CONTENT PRESERVATION REQUIREMENT:
- You MUST preserve ALL original sections and paragraphs
- You MUST NOT delete any existing content
- You MUST NOT shorten existing sections
- You MUST NOT remove examples, explanations, or details from the original
- You can only ADD to the document, never subtract

{focus_text}
{score_context}
{structured_context}

=== ORIGINAL DOCUMENT ({document_type}) ===

{original_document}

=== QUALITY REVIEW FEEDBACK ===

{quality_feedback}

=== YOUR TASK ===

Generate an IMPROVED version of the document by ADDING information that:
1. PRESERVES all existing content and structure (100% of original content must remain)
2. ADDS missing sections with substantial, high-quality content
3. EXPANDS existing sections with more detail, examples, and explanations
4. ADDS clarifications and improvements without removing original text
5. ADDRESSES all issues mentioned in the quality feedback by adding content
6. MAINTAINS professional quality and consistency
7. MEETS all quality metric requirements (word count, sections, readability)
8. IS LONGER than the original document (add at least 10-20% more content)

IMPORTANT: This is an ADDITIVE improvement. Keep ALL original content and structure. Only ADD:
- Missing sections (add them in appropriate locations)
- More detail to existing sections (expand with examples, explanations)
- Clarifications and improvements (add without removing original text)

DO NOT:
- Remove or rewrite existing content
- Change the document structure significantly
- Delete any existing sections or paragraphs
- Make the document shorter than the original
- Remove examples, explanations, or details from the original

Start directly with the improved document content (preserving original structure):"""
        
        try:
            logger.debug(f"Improving {document_type} document (original: {len(original_document)} chars)")
            improved_doc = self._call_llm(prompt, temperature=0.5)  # Lower temperature for more consistent improvements
            
            # Clean the response
            improved_doc = improved_doc.strip()
            
            # Remove markdown code blocks if present
            if improved_doc.startswith("```"):
                lines = improved_doc.split("\n")
                if len(lines) > 2:
                    improved_doc = "\n".join(lines[1:-1])
            
            logger.debug(f"Improved document generated ({len(improved_doc)} chars)")
            return improved_doc
            
        except Exception as e:
            logger.error(f"Error improving document: {e}")
            raise
    
    def improve_and_save(
        self,
        original_document: str,
        document_type: str,
        quality_feedback: str,
        output_filename: str,
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None,
        agent_type: Optional[AgentType] = None
    ) -> str:
        """
        Improve document and save to file
        
        Args:
            original_document: Original document content
            document_type: Type of document
            quality_feedback: Quality review feedback
            output_filename: Output filename
            project_id: Project ID
            context_manager: Context manager
            agent_type: Agent type for context saving
        
        Returns:
            Path to saved improved document
        """
        logger.info(f"Improving {document_type} based on quality feedback")
        
        # Improve the document
        improved_doc = self.improve_document(original_document, document_type, quality_feedback)
        
        # Save to file (overwrite original)
        file_path = self.file_manager.write_file(output_filename, improved_doc)
        logger.info(f"Improved {document_type} saved to: {file_path}")
        
        # Save to context if available
        if project_id and context_manager and agent_type:
            try:
                output = AgentOutput(
                    agent_type=agent_type,
                    document_type=document_type,
                    content=improved_doc,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
                logger.debug(f"Improved {document_type} saved to context")
            except Exception as e:
                logger.warning(f"Could not save improved document to context: {e}")
        
        return file_path


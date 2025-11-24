"""
Quality Reviewer Agent
Reviews and improves all generated documentation
"""
from typing import Optional, Dict
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.quality.quality_checker import QualityChecker
from src.quality.document_type_quality_checker import DocumentTypeQualityChecker
from src.rate_limit.queue_manager import RequestQueue
from prompts.system_prompts import get_quality_reviewer_prompt, get_structured_quality_feedback_prompt
import json
import re


class QualityReviewerAgent(BaseAgent):
    """
    Quality Reviewer Agent
    
    Reviews all generated documentation and provides:
    - Overall quality assessment
    - Completeness analysis
    - Clarity and readability review
    - Consistency checks
    - Technical accuracy review
    - Improvement suggestions
    - Quality metrics
    """
    
    def __init__(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        rate_limiter: Optional[RequestQueue] = None,
        file_manager: Optional[FileManager] = None,
        quality_checker: Optional[QualityChecker] = None,
        api_key: Optional[str] = None,
        **provider_kwargs
    ):
        """Initialize Quality Reviewer Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager(base_dir="docs/quality")
        self.quality_checker = quality_checker or QualityChecker()
        # Use document-type-aware quality checker for better accuracy
        self.document_type_checker = DocumentTypeQualityChecker()
    
    def generate(self, all_documentation: Dict[str, str]) -> str:
        """
        Generate quality review report from all documentation
        
        Args:
            all_documentation: Dict mapping document names to their content
        
        Returns:
            Generated quality review report (Markdown)
        """
        # First run automated quality checks using document-type-aware checker
        automated_scores = {}
        for doc_name, doc_content in all_documentation.items():
            try:
                # Use document-type-aware checker for better accuracy
                quality_result = self.document_type_checker.check_multiple_documents(
                    {doc_name: doc_content}
                ).get(doc_name, {})
                
                # Fallback to base checker if document-type checker fails
                if not quality_result or quality_result.get("error"):
                    quality_result = self.quality_checker.check_quality(doc_content)
                
                automated_scores[doc_name] = quality_result
            except Exception as e:
                # Skip quality check for this document if it fails
                automated_scores[doc_name] = {
                    "overall_score": 0,
                    "passed": False,
                    "error": str(e),
                    "word_count": {"word_count": 0},
                    "sections": {"completeness_score": 0, "found_count": 0, "required_count": 0},
                    "readability": {"readability_score": 0, "level": "unknown"}
                }
        
        # Get prompt from centralized prompts config
        full_prompt = get_quality_reviewer_prompt(all_documentation)
        
        # Add automated scores to prompt for LLM context
        if automated_scores:
            scores_summary = "\n\n## Automated Quality Scores:\n"
            for doc_name, score_data in automated_scores.items():
                scores_summary += f"\n### {doc_name}\n"
                scores_summary += f"- Overall Score: {score_data.get('overall_score', 0):.1f}/100\n"
                # Fix: Access word_count directly from the result structure
                word_count_data = score_data.get('word_count', {})
                sections_data = score_data.get('sections', {})
                readability_data = score_data.get('readability', {})
                
                scores_summary += f"- Word Count: {word_count_data.get('word_count', 0)} (min: {word_count_data.get('min_threshold', 100)}, passed: {word_count_data.get('passed', False)})\n"
                scores_summary += f"- Section Completeness: {sections_data.get('completeness_score', 0):.1f}% ({sections_data.get('found_count', 0)}/{sections_data.get('required_count', 0)} sections found, passed: {sections_data.get('passed', False)})\n"
                scores_summary += f"- Readability Score: {readability_data.get('readability_score', 0):.1f} ({readability_data.get('level', 'unknown')}, passed: {readability_data.get('passed', False)})\n"
                if sections_data.get('missing_sections'):
                    # Extract and clean missing sections (f-string can't contain backslashes)
                    missing = sections_data.get('missing_sections', [])[:3]
                    cleaned = [s.replace('^#+\\s+', '').replace('\\s+', ' ') for s in missing]
                    scores_summary += f"- Missing Sections: {', '.join(cleaned)}\n"
                
                # Add auto_fail violations if present
                auto_fail = score_data.get('auto_fail', {})
                if auto_fail and not auto_fail.get('auto_fail_passed', True):
                    violations = auto_fail.get('auto_fail_violations', [])
                    scores_summary += f"- ⚠️ AUTO-FAIL VIOLATIONS: {', '.join(violations)}\n"
                
                # Add LLM focus questions if available
                llm_focus = score_data.get('llm_focus', [])
                if llm_focus:
                    scores_summary += f"- Focus Questions: {', '.join(llm_focus)}\n"
            
            full_prompt += scores_summary + "\n\nConsider these automated scores in your review. Focus on improving documents with low scores."
        
        
        stats = self.get_stats()
        
        try:
            review_report = self._call_llm(full_prompt)
            return review_report
        except Exception as e:
            raise
    
    def generate_and_save(
        self,
        all_documentation: Dict[str, str],
        output_filename: str = "quality_review.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Generate quality review and save to file
        
        Args:
            all_documentation: Dict mapping document names to their content
            output_filename: Filename to save
            project_id: Project ID for context sharing
            context_manager: Context manager for saving
            
        Returns:
            Absolute path to saved file
        """
        # Generate review report
        review_report = self.generate(all_documentation)
        
        # Generate virtual file path for reference (not used for actual file storage)
        virtual_path = f"docs/{output_filename}"
        logger.info(f"Quality review report saving to database (virtual path: {virtual_path})")
        
        # Save to database
        try:
            if project_id and context_manager:
                output = AgentOutput(
                    agent_type=AgentType.QUALITY_REVIEWER,
                    document_type="quality_review",
                    content=review_report,
                    file_path=virtual_path,  # Virtual path for reference only
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
                logger.info("✅ Quality review report saved to database")
            else:
                logger.warning("⚠️  No context manager available, review report not saved")
            
            return virtual_path  # Return virtual path for compatibility
        except Exception as e:
            raise
    
    def generate_structured_feedback(
        self,
        document_content: str,
        document_type: str,
        automated_scores: Optional[Dict] = None
    ) -> Dict:
        """
        Generate structured JSON feedback for a single document (LLM-as-Judge)
        
        This method uses LLM to generate structured, actionable feedback in JSON format
        that can be directly used by DocumentImproverAgent for precise improvements.
        
        Args:
            document_content: The document content to review
            document_type: Type of document (e.g., "api_documentation", "technical_documentation")
            automated_scores: Optional automated quality scores from QualityChecker
        
        Returns:
            Dict with structured feedback:
            {
                "score": float (1-10),
                "feedback": str,
                "suggestion": str,
                "missing_sections": List[str],
                "strengths": List[str],
                "weaknesses": List[str],
                "readability_issues": List[str],
                "priority_improvements": List[Dict]
            }
        """
        # Get LLM focus questions from automated_scores if available
        llm_focus = automated_scores.get("llm_focus", []) if automated_scores else []
        
        # Get structured feedback prompt (with llm_focus if available)
        prompt = get_structured_quality_feedback_prompt(
            document_content=document_content,
            document_type=document_type,
            automated_scores=automated_scores,
            llm_focus_questions=llm_focus
        )
        
        try:
            # Call LLM to generate structured feedback
            response = self._call_llm(prompt)
            
            # Extract JSON from response (handle cases where LLM adds markdown or explanations)
            json_match = re.search(r'\{[^{}]*"score"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try to find JSON in code blocks
                json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_block:
                    json_str = json_block.group(1)
                else:
                    # Try to parse entire response as JSON
                    json_str = response.strip()
            
            # Parse JSON
            try:
                feedback_data = json.loads(json_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key fields manually
                logger.warning(f"Failed to parse JSON feedback, attempting fallback extraction")
                feedback_data = self._extract_feedback_fallback(response)
            
            # Validate and normalize feedback structure
            feedback_data = self._validate_feedback_structure(feedback_data)
            
            return feedback_data
            
        except Exception as e:
            logger.error(f"Error generating structured feedback: {e}", exc_info=True)
            # Return fallback feedback structure
            return {
                "score": automated_scores.get("overall_score", 5.0) / 10.0 if automated_scores else 5.0,
                "feedback": f"Quality review failed: {str(e)}",
                "suggestion": "Review the document manually and check for completeness and clarity",
                "missing_sections": automated_scores.get("sections", {}).get("missing_sections", [])[:5] if automated_scores else [],
                "strengths": [],
                "weaknesses": ["Quality review generation failed"],
                "readability_issues": [],
                "priority_improvements": []
            }
    
    def _extract_feedback_fallback(self, response: str) -> Dict:
        """Extract feedback from response when JSON parsing fails"""
        feedback_data = {
            "score": 5.0,
            "feedback": response[:200] if len(response) > 200 else response,
            "suggestion": "Improve document structure and completeness",
            "missing_sections": [],
            "strengths": [],
            "weaknesses": [],
            "readability_issues": [],
            "priority_improvements": []
        }
        
        # Try to extract score
        score_match = re.search(r'"score"\s*:\s*([\d.]+)', response)
        if score_match:
            try:
                feedback_data["score"] = float(score_match.group(1))
            except ValueError:
                pass
        
        # Try to extract suggestion
        suggestion_match = re.search(r'"suggestion"\s*:\s*"([^"]+)"', response)
        if suggestion_match:
            feedback_data["suggestion"] = suggestion_match.group(1)
        
        return feedback_data
    
    def _validate_feedback_structure(self, feedback_data: Dict) -> Dict:
        """Validate and normalize feedback structure"""
        # Ensure all required fields exist
        validated = {
            "score": float(feedback_data.get("score", 5.0)),
            "feedback": str(feedback_data.get("feedback", "No feedback provided")),
            "suggestion": str(feedback_data.get("suggestion", "Review document for improvements")),
            "missing_sections": list(feedback_data.get("missing_sections", [])),
            "strengths": list(feedback_data.get("strengths", [])),
            "weaknesses": list(feedback_data.get("weaknesses", [])),
            "readability_issues": list(feedback_data.get("readability_issues", [])),
            "priority_improvements": list(feedback_data.get("priority_improvements", []))
        }
        
        # Ensure score is in valid range
        validated["score"] = max(1.0, min(10.0, validated["score"]))
        
        # Ensure lists are strings
        for key in ["missing_sections", "strengths", "weaknesses", "readability_issues"]:
            validated[key] = [str(item) for item in validated[key]]
        
        # Validate priority_improvements structure
        validated_priorities = []
        for item in validated["priority_improvements"]:
            if isinstance(item, dict):
                validated_priorities.append({
                    "area": str(item.get("area", "Unknown")),
                    "issue": str(item.get("issue", "")),
                    "suggestion": str(item.get("suggestion", ""))
                })
        validated["priority_improvements"] = validated_priorities
        
        return validated


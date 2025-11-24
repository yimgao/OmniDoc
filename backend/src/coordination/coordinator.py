"""Configuration-driven workflow coordinator for OmniDoc."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union, Set
import re
import asyncio
import time
import sys

from src.agents.generic_document_agent import GenericDocumentAgent
from src.agents.special_agent_adapter import SpecialAgentAdapter
from src.agents.special_agent_registry import get_special_agent_class
from src.agents.quality_reviewer_agent import QualityReviewerAgent
from src.agents.document_improver_agent import DocumentImproverAgent
from src.config.document_catalog import (
    DocumentDefinition,
    load_document_definitions,
    resolve_dependencies,
    get_all_dependencies,
)
from src.config.settings import get_settings
from src.context.context_manager import ContextManager
from src.utils.logger import get_logger
from src.coordination.metrics import get_metrics, clear_metrics

logger = get_logger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class WorkflowCoordinator:
    """Coordinates configuration-driven document generation."""
    
    def __init__(
        self,
        context_manager: Optional[ContextManager] = None,
        provider_name: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.context_manager = context_manager or ContextManager()
        self.definitions: Dict[str, DocumentDefinition] = load_document_definitions()
        self.provider_name = (provider_name or settings.default_llm_provider or "gemini").lower()
        self.output_root = Path(settings.docs_dir) / "projects"
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.agents = self._build_agents()
        
        # Initialize quality review and improvement agents
        self.quality_reviewer = QualityReviewerAgent(provider_name=self.provider_name)
        self.document_improver = DocumentImproverAgent(provider_name=self.provider_name)

    def _build_agents(self) -> Dict[str, Union[GenericDocumentAgent, SpecialAgentAdapter]]:
        """Build agents dictionary, using special agents when configured."""
        agents: Dict[str, Union[GenericDocumentAgent, SpecialAgentAdapter]] = {}
        for definition in self.definitions.values():
            if definition.agent_class == "special":
                # Try to get special agent class
                special_agent_class = get_special_agent_class(definition.id, definition.special_key)
                if special_agent_class:
                    logger.debug("Using special agent %s for document %s", special_agent_class.__name__, definition.id)
                    special_agent = special_agent_class(provider_name=self.provider_name)
                    agents[definition.id] = SpecialAgentAdapter(
                        agent=special_agent,
                        definition=definition,
                        base_output_dir=str(self.output_root),
                        context_manager=self.context_manager,
                    )
                else:
                    logger.warning(
                        "Document %s marked as special but no special agent found, falling back to generic",
                        definition.id,
                    )
                    agents[definition.id] = GenericDocumentAgent(
                        definition=definition,
                        provider_name=self.provider_name,
                        base_output_dir=str(self.output_root),
                    )
            else:
                # Use generic agent
                agents[definition.id] = GenericDocumentAgent(
                    definition=definition,
                    provider_name=self.provider_name,
                    base_output_dir=str(self.output_root),
                    context_manager=self.context_manager,
                )
        return agents

    async def _review_and_improve_document(
        self,
        document_id: str,
        document_name: str,
        document_type: str,
        original_content: str,
        user_idea: str,
        dependency_documents: Dict[str, Dict[str, str]],
        agent: Union[GenericDocumentAgent, SpecialAgentAdapter],
        output_rel_path: str,
        project_id: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> str:
        """
        Review document quality and improve if needed.
        
        Workflow:
        1. Quality reviewer checks if content is good
        2. If not good, document improver identifies specific issues
        3. Document agent regenerates only problematic sections
        4. Merge improved sections back into original document
        
        Returns:
            Improved document content (or original if no improvements needed)
        """
        try:
            # Step 1: Quality Review
            if progress_callback:
                await progress_callback(
                    {
                        "type": "quality_review_started",
                        "project_id": project_id,
                        "document_id": document_id,
                        "name": document_name,
                    }
                )
            
            # Extract sections for logging
            original_sections = self._extract_sections(original_content)
            logger.info(
                "🔍 Reviewing quality of document %s [Project: %s] [Content length: %d chars] [Sections: %d]",
                document_id,
                project_id,
                len(original_content),
                len(original_sections)
            )
            
            if original_sections:
                logger.debug(
                    "📋 Original document sections for %s [Project: %s]: %s",
                    document_id,
                    project_id,
                    ", ".join(original_sections[:10])  # Show first 10 sections
                )
            
            # Get automated quality scores first (to include llm_focus and auto_fail)
            from src.quality.document_type_quality_checker import DocumentTypeQualityChecker
            doc_type_checker = DocumentTypeQualityChecker()
            automated_scores = doc_type_checker.check_quality_for_type(
                content=original_content,
                document_type=document_name  # Use document name for better matching
            )
            
            # Check for auto_fail conditions
            auto_fail_info = automated_scores.get("auto_fail", {})
            auto_fail_triggered = not auto_fail_info.get("auto_fail_passed", True) if auto_fail_info else False
            auto_fail_reasons = auto_fail_info.get("auto_fail_violations", []) if auto_fail_info else []
            
            if auto_fail_triggered:
                logger.warning(
                    "🚨 AUTO-FAIL triggered for %s [Project: %s]: %s",
                    document_id,
                    project_id,
                    ", ".join(auto_fail_reasons) if auto_fail_reasons else "Auto-fail conditions met"
                )
            
            # Get structured feedback from quality reviewer (sync method, run in executor)
            loop = asyncio.get_event_loop()
            structured_feedback_dict = await loop.run_in_executor(
                None,
                lambda: self.quality_reviewer.generate_structured_feedback(
                    document_content=original_content,
                    document_type=document_type,
                    automated_scores=automated_scores
                )
            )
            
            quality_score = structured_feedback_dict.get("score", 5.0)
            
            # Step 2: Force improvement if auto_fail is triggered (even if score is high)
            if auto_fail_triggered:
                # Force quality score below threshold to ensure improvement
                if quality_score >= 7.0:
                    logger.info(
                        "🔧 Forcing improvement for %s due to auto-fail conditions [Original score: %.1f/10] [Project: %s]",
                        document_id,
                        quality_score,
                        project_id
                    )
                    quality_score = 6.5  # Force below threshold
                    structured_feedback_dict["score"] = quality_score
                    structured_feedback_dict["forced_improvement"] = True
                    structured_feedback_dict["auto_fail_reasons"] = auto_fail_reasons
            
            logger.info(
                "📊 Quality score for %s: %.1f/10 [Project: %s] [Auto-fail: %s]",
                document_id,
                quality_score,
                project_id,
                "YES" if auto_fail_triggered else "NO"
            )
            
            # Step 3: Check if improvement is needed (threshold: 7.0/10)
            if quality_score >= 7.0:
                logger.info(
                    "✅ Document %s quality is acceptable [Project: %s] [Score: %.1f/10] [Skipping improvement]",
                    document_id,
                    project_id,
                    quality_score
                )
                if progress_callback:
                    await progress_callback(
                        {
                            "type": "quality_review_completed",
                            "project_id": project_id,
                            "document_id": document_id,
                            "name": document_name,
                            "score": quality_score,
                            "needs_improvement": False,
                        }
                    )
                return original_content
            
            # Step 3: Document needs improvement
            logger.info(
                "🔧 Document %s needs improvement [Score: %.1f/10] [Project: %s]",
                document_id,
                quality_score,
                project_id
            )
            
            # Get improvement feedback details (for internal use, not logged)
            issues = structured_feedback_dict.get("issues", [])
            suggestions = structured_feedback_dict.get("improvement_suggestions", [])
            
            if issues:
                logger.debug(
                    "🔍 Issues identified for %s [Project: %s]: %s",
                    document_id,
                    project_id,
                    issues[:5]  # Log first 5 issues
                )
            
            if progress_callback:
                await progress_callback(
                    {
                        "type": "quality_review_completed",
                        "project_id": project_id,
                        "document_id": document_id,
                        "name": document_name,
                        "score": quality_score,
                        "needs_improvement": True,
                    }
                )
            
            # Step 4: Document improver identifies specific issues and generates improvement suggestions
            if progress_callback:
                await progress_callback(
                    {
                        "type": "improvement_started",
                        "project_id": project_id,
                        "document_id": document_id,
                        "name": document_name,
                    }
                )
            
            # Get improvement suggestions from document improver
            improvement_suggestions = structured_feedback_dict.get("priority_improvements", [])
            missing_sections = structured_feedback_dict.get("missing_sections", [])
            weaknesses = structured_feedback_dict.get("weaknesses", [])
            
            # Build quality feedback text for document improver
            quality_feedback_text = f"""Quality Review Results:
- Quality Score: {quality_score:.1f}/10
- Overall Feedback: {structured_feedback_dict.get('feedback', 'No feedback')}
- Primary Suggestion: {structured_feedback_dict.get('suggestion', 'No specific suggestion')}

Issues Identified:
"""
            if missing_sections:
                quality_feedback_text += f"- Missing Sections: {', '.join(missing_sections)}\n"
            if weaknesses:
                quality_feedback_text += "- Weaknesses:\n"
                for weakness in weaknesses:
                    quality_feedback_text += f"  • {weakness}\n"
            if improvement_suggestions:
                quality_feedback_text += "- Priority Improvements:\n"
                for improvement in improvement_suggestions[:5]:  # Limit to top 5
                    if isinstance(improvement, dict):
                        quality_feedback_text += f"  • {improvement.get('area', 'Unknown')}: {improvement.get('issue', '')}\n"
                        quality_feedback_text += f"    → Suggestion: {improvement.get('suggestion', '')}\n"
            
            # Step 5: Use document improver to generate improved version
            # Call improve_document in async context
            loop = asyncio.get_event_loop()
            improved_content = await loop.run_in_executor(
                None,
                lambda: self.document_improver.improve_document(
                    original_document=original_content,
                    document_type=document_type,
                    quality_feedback=quality_feedback_text,
                    structured_feedback=structured_feedback_dict,
                )
            )
            
            # Step 6: Merge improved sections back into original
            # The document improver should preserve original structure and add improvements
            # If it doesn't, we'll use a smart merge strategy
            merged_content = self._merge_improved_content(
                original_content=original_content,
                improved_content=improved_content,
                structured_feedback={**structured_feedback_dict, "document_type": document_type},
            )
            
            # Step 7: Validate improved content
            validation_result = self._validate_improved_content(
                original_content=original_content,
                improved_content=merged_content,
                document_type=document_type,
                document_id=document_id,
                project_id=project_id,
            )
            
            # If validation fails critically, log warning but still use improved content
            if not validation_result.get("passed", True):
                logger.warning(
                    "⚠️ Improved content validation failed for %s [Project: %s]: %s",
                    document_id,
                    project_id,
                    validation_result.get("warnings", [])
                )
            
            improvement_ratio = (len(merged_content) / len(original_content)) * 100 if original_content else 0
            
            # Extract sections for comparison
            improved_sections = self._extract_sections(merged_content)
            section_change = len(improved_sections) - len(original_sections)
            
            logger.info(
                "✅ Document %s improved [Project: %s] [Original: %d chars, %d sections] [Improved: %d chars, %d sections] [Change: %.1f%% chars, %+d sections]",
                document_id,
                project_id,
                len(original_content),
                len(original_sections),
                len(merged_content),
                len(improved_sections),
                improvement_ratio - 100,
                section_change
            )
            
            # Log section comparison if there are changes
            if section_change != 0:
                added_sections = set(improved_sections) - set(original_sections)
                removed_sections = set(original_sections) - set(improved_sections)
                
                if added_sections:
                    logger.info(
                        "➕ Added sections to %s [Project: %s]: %s",
                        document_id,
                        project_id,
                        ", ".join(list(added_sections)[:5])
                    )
                
                if removed_sections:
                    logger.warning(
                        "➖ Removed sections from %s [Project: %s]: %s",
                        document_id,
                        project_id,
                        ", ".join(list(removed_sections)[:5])
                    )
            
            if progress_callback:
                await progress_callback(
                    {
                        "type": "improvement_completed",
                        "project_id": project_id,
                        "document_id": document_id,
                        "name": document_name,
                        "original_length": len(original_content),
                        "improved_length": len(merged_content),
                    }
                )
            
            return merged_content
            
        except Exception as e:
            logger.error(f"❌ Error during quality review/improvement for {document_id}: {e}", exc_info=True)
            # Return original content if improvement fails
            return original_content
    
    def _merge_improved_content(
        self,
        original_content: str,
        improved_content: str,
        structured_feedback: Dict,
    ) -> str:
        """
        Merge improved content back into original document.
        
        Strategy:
        1. If improved content is significantly longer and contains original structure, use improved
        2. If improved content is shorter, check if it's still complete (has all required sections)
        3. If improved content is significantly shorter and missing sections, log warning but use improved
        4. Add detailed logging for content comparison
        """
        original_length = len(original_content)
        improved_length = len(improved_content)
        length_ratio = improved_length / original_length if original_length > 0 else 1.0
        
        # Extract sections for comparison
        original_sections = self._extract_sections(original_content)
        improved_sections = self._extract_sections(improved_content)
        
        # Log detailed comparison
        logger.info(
            "📊 Content merge analysis [Original: %d chars, %d sections] [Improved: %d chars, %d sections] [Ratio: %.1f%%]",
            original_length,
            len(original_sections),
            improved_length,
            len(improved_sections),
            length_ratio * 100
        )
        
        # Check if improved content is significantly shorter (more than 20% reduction)
        if length_ratio < 0.8:
            logger.warning(
                "⚠️ Improved content is %.1f%% shorter than original [Original: %d chars] [Improved: %d chars]",
                (1 - length_ratio) * 100,
                original_length,
                improved_length
            )
            
            # Check if improved content has fewer sections
            if len(improved_sections) < len(original_sections) * 0.8:
                missing_sections = set(original_sections) - set(improved_sections)
                logger.warning(
                    "⚠️ Improved content is missing %d sections: %s",
                    len(missing_sections),
                    ", ".join(list(missing_sections)[:5])  # Show first 5
                )
            
            # Check if improved content has all required sections from quality rules
            try:
                from src.quality.document_type_quality_checker import DocumentTypeQualityChecker
                checker = DocumentTypeQualityChecker()
                # Try to get document type from structured_feedback or use a default
                document_type = structured_feedback.get("document_type", "document")
                requirements = checker.get_requirements_for_type(document_type)
                required_sections = requirements.get("required_sections", [])
                
                if required_sections:
                    # Check if improved content has all required sections
                    improved_section_names = [s.lower() for s in improved_sections]
                    missing_required = []
                    for req_section_pattern in required_sections:
                        # Convert regex pattern to simple name for comparison
                        req_section_clean = req_section_pattern.replace("^#+\\s+", "").replace("\\s+", " ").lower()
                        found = any(req_section_clean in section.lower() or section.lower() in req_section_clean 
                                   for section in improved_sections)
                        if not found:
                            missing_required.append(req_section_pattern.replace("^#+\\s+", "").replace("\\s+", " "))
                    
                    if missing_required:
                        logger.error(
                            "❌ Improved content is missing REQUIRED sections: %s. This is a critical issue.",
                            ", ".join(missing_required)
                        )
                        # Still use improved content, but log the error
                    else:
                        logger.info("✅ Improved content contains all required sections despite being shorter")
            except Exception as e:
                logger.debug(f"Could not verify required sections: {e}")
        
        # If improved content is significantly longer and has most sections, use it
        if length_ratio > 1.2 and len(improved_sections) >= len(original_sections) * 0.8:
            logger.info("✅ Using improved content (significantly longer and complete)")
            return improved_content
        
        # If improved content is shorter but still has most sections, use it (document improver should preserve structure)
        if len(improved_sections) >= len(original_sections) * 0.8:
            logger.info("✅ Using improved content (has most original sections)")
            return improved_content
        
        # If improved content is significantly shorter and missing many sections, log warning but still use it
        # (The document improver should have preserved structure, so this might indicate a real issue)
        logger.warning(
            "⚠️ Improved content is shorter and missing sections, but using it anyway. "
            "Document improver should have preserved structure."
        )
        return improved_content
    
    def _extract_sections(self, content: str) -> List[str]:
        """Extract section headings from markdown content."""
        # Match markdown headings (# ## ### etc.)
        heading_pattern = r'^#{1,6}\s+(.+)$'
        sections = []
        for line in content.split('\n'):
            match = re.match(heading_pattern, line)
            if match:
                sections.append(match.group(1).strip())
        return sections
    
    def _validate_improved_content(
        self,
        original_content: str,
        improved_content: str,
        document_type: str,
        document_id: str,
        project_id: str,
    ) -> Dict:
        """
        Validate improved content to ensure it hasn't lost critical information.
        
        Returns:
            Dict with 'passed' (bool) and 'warnings' (list of strings)
        """
        validation_result = {
            "passed": True,
            "warnings": [],
        }
        
        original_length = len(original_content)
        improved_length = len(improved_content)
        length_ratio = improved_length / original_length if original_length > 0 else 1.0
        
        # Check 1: Content length validation
        if length_ratio < 0.9:  # More than 10% reduction
            validation_result["warnings"].append(
                f"Improved content is {((1 - length_ratio) * 100):.1f}% shorter than original "
                f"({original_length:,} → {improved_length:,} chars)"
            )
            if length_ratio < 0.8:  # More than 20% reduction
                validation_result["passed"] = False
        
        # Check 2: Section preservation validation
        original_sections = self._extract_sections(original_content)
        improved_sections = self._extract_sections(improved_content)
        
        if len(improved_sections) < len(original_sections) * 0.8:
            missing_sections = set(original_sections) - set(improved_sections)
            validation_result["warnings"].append(
                f"Improved content is missing {len(missing_sections)} sections: "
                f"{', '.join(list(missing_sections)[:5])}"
            )
            if len(improved_sections) < len(original_sections) * 0.7:
                validation_result["passed"] = False
        
        # Check 3: Required sections validation (from quality rules)
        try:
            from src.quality.document_type_quality_checker import DocumentTypeQualityChecker
            checker = DocumentTypeQualityChecker()
            requirements = checker.get_requirements_for_type(document_type)
            required_sections = requirements.get("required_sections", [])
            
            if required_sections:
                improved_section_names = [s.lower() for s in improved_sections]
                missing_required = []
                for req_section_pattern in required_sections:
                    req_section_clean = req_section_pattern.replace("^#+\\s+", "").replace("\\s+", " ").lower()
                    found = any(req_section_clean in section.lower() or section.lower() in req_section_clean 
                               for section in improved_sections)
                    if not found:
                        missing_required.append(req_section_pattern.replace("^#+\\s+", "").replace("\\s+", " "))
                
                if missing_required:
                    validation_result["warnings"].append(
                        f"Improved content is missing REQUIRED sections: {', '.join(missing_required)}"
                    )
                    validation_result["passed"] = False
        except Exception as e:
            logger.debug(f"Could not validate required sections: {e}")
        
        # Log validation result
        if validation_result["passed"]:
            logger.info(
                "✅ Improved content validation passed for %s [Project: %s]",
                document_id,
                project_id
            )
        else:
            logger.warning(
                "⚠️ Improved content validation failed for %s [Project: %s]: %s",
                document_id,
                project_id,
                "; ".join(validation_result["warnings"])
            )
        
        return validation_result

    async def _generate_single_doc(
        self,
        document_id: str,
        project_id: str,
        user_idea: str,
        generated_docs: Dict[str, Dict[str, str]],
        progress_callback: Optional[ProgressCallback],
        total: int,
        completed_count: int
    ) -> Dict:
        """
        Generate a single document. Helper for parallel execution.
        """
        definition = self.definitions.get(document_id)
        if not definition:
            logger.error("Unknown document id '%s' [Project: %s]", document_id, project_id)
            raise ValueError(f"Unknown document id '{document_id}'.")

        agent = self.agents.get(document_id)
        if not agent:
            logger.error("No agent available for document '%s' [Project: %s]", document_id, project_id)
            raise ValueError(f"No agent available for document '{document_id}'.")

        # Build dependency payload
        all_dependencies = get_all_dependencies(document_id)
        
        # Check for missing dependencies
        missing_dependencies = [
            dep for dep in all_dependencies
            if dep not in generated_docs
        ]
        
        if missing_dependencies:
            logger.warning(
                "⚠️ Missing dependencies for document %s: %s [Project: %s]. Continuing.",
                document_id, missing_dependencies, project_id
            )
            if progress_callback:
                await progress_callback({
                    "type": "warning",
                    "project_id": project_id,
                    "document_id": document_id,
                    "name": definition.name,
                    "message": f"Missing dependencies: {', '.join(missing_dependencies)}.",
                    "missing_dependencies": missing_dependencies,
                })
        
        dependency_payload = {
            dep: generated_docs[dep] for dep in all_dependencies if dep in generated_docs
        }
        
        # Add implicit context for certain documents
        if not dependency_payload and document_id in ["gtm_strategy", "marketing_plan"]:
            for useful_doc_id in ["project_charter", "business_model", "requirements"]:
                if useful_doc_id in generated_docs:
                    dependency_payload[useful_doc_id] = generated_docs[useful_doc_id]

        if progress_callback:
            await progress_callback({
                "type": "document_started",
                "project_id": project_id,
                "document_id": document_id,
                "name": definition.name,
                "index": str(completed_count + 1), # Approximate index
                "total": str(total),
            })

        output_rel_path = f"{project_id}/{document_id}.md"
        
        if isinstance(agent, SpecialAgentAdapter):
            agent.project_id = project_id
            agent.context_manager = self.context_manager
        
        doc_start_time = time.time()
        try:
            logger.info(f"📝 Starting generation for {document_id} [Project: {project_id}]")
            document_timeout = 1800
            
            document_result = await asyncio.wait_for(
                agent.generate_and_save(
                    user_idea=user_idea,
                    dependency_documents=dependency_payload,
                    output_rel_path=output_rel_path,
                    project_id=project_id,
                ),
                timeout=document_timeout
            )
            
            # Quality Review
            original_content = document_result.get("content", "")
            if original_content:
                improved_content = await self._review_and_improve_document(
                    document_id=document_id,
                    document_name=definition.name,
                    document_type=definition.category or "document",
                    original_content=original_content,
                    user_idea=user_idea,
                    dependency_documents=dependency_payload,
                    agent=agent,
                    output_rel_path=output_rel_path,
                    project_id=project_id,
                    progress_callback=progress_callback,
                )
                if improved_content and improved_content != original_content:
                    document_result["content"] = improved_content
                    # Update DB
                    try:
                        from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
                        try:
                            agent_type = AgentType(document_id)
                        except ValueError:
                            try:
                                agent_type = AgentType.TECHNICAL_DOCUMENTATION
                            except:
                                agent_type = list(AgentType)[0]
                        
                        output = AgentOutput(
                            agent_type=agent_type,
                            document_type=document_id,
                            content=improved_content,
                            file_path=document_result.get("file_path"),
                            status=DocumentStatus.COMPLETE,
                            quality_score=document_result.get("quality_score"),
                        )
                        self.context_manager.save_agent_output(project_id, output)
                    except Exception as e:
                        logger.error(f"Failed to save improved content for {document_id}: {e}")

            if progress_callback:
                await progress_callback({
                    "type": "document_completed",
                    "project_id": project_id,
                    "document_id": document_id,
                    "name": definition.name,
                    "index": str(completed_count + 1),
                    "total": str(total),
                })
                
            return document_id, document_result

        except Exception as e:
            logger.error(f"Failed to generate {document_id}: {e}", exc_info=True)
            if progress_callback:
                await progress_callback({
                    "type": "error",
                    "project_id": project_id,
                    "document_id": document_id,
                    "name": definition.name,
                    "error": str(e),
                })
            raise

    async def async_generate_all_docs(
        self,
        user_idea: str,
        project_id: str,
        selected_documents: List[str],
        codebase_path: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Dict]:
        del codebase_path

        if not selected_documents:
            raise ValueError("No documents selected for generation.")

        try:
            # Get topological sort to ensure order is respected in fallback, but we use DAG for parallel
            execution_plan = resolve_dependencies(selected_documents)
        except ValueError as exc:
            logger.info("Dependency resolution issue: %s", exc)
            raise
        
        total = len(execution_plan)
        generated_docs: Dict[str, Dict[str, str]] = {}
        results: Dict[str, Dict] = {"files": {}, "documents": []}
        
        completed_docs: Set[str] = set()
        # Note: execution_plan includes selected docs AND their dependencies.
        # We need to process ALL of them.
        pending_docs = set(execution_plan)
        
        workflow_start_time = time.time()
        logger.info(f"🚀 Starting PARALLEL workflow [Project: {project_id}] [Total: {total}]")
        
        # Initialize metrics tracking
        metrics = get_metrics(project_id)
        metrics.total_documents = total

        if progress_callback:
            await progress_callback({
                "type": "plan",
                "project_id": project_id,
                "documents": ",".join(execution_plan),
                "total": str(total),
            })

        # Loop until all documents are processed
        wave_number = 0
        while pending_docs:
            wave_number += 1
            wave_start_time = time.time()
            
            # Find documents whose dependencies are all met
            ready_batch = []
            for doc_id in pending_docs:
                deps = get_all_dependencies(doc_id)
                # Check if all dependencies are in completed_docs
                # Note: Deps must be in 'generated_docs' which implies they finished successfully.
                if all(dep in completed_docs for dep in deps if dep in execution_plan):
                    # Also verify deps that are NOT in execution plan (e.g. pre-existing)? 
                    # resolve_dependencies ensures all needed deps are in the plan.
                    ready_batch.append(doc_id)
            
            if not ready_batch:
                # This shouldn't happen if resolve_dependencies passed, unless there's a logic bug
                # or a cycle passed through (unlikely).
                logger.error("Deadlock detected in generation: pending docs have unmet dependencies but no progress can be made.")
                logger.error(f"Pending: {pending_docs}")
                logger.error(f"Completed: {completed_docs}")
                break

            # Sort batch to be deterministic (e.g. by index in execution_plan) to reduce chaos
            ready_batch.sort(key=lambda x: execution_plan.index(x))
            
            logger.info(f"⚡ Processing parallel batch {wave_number}: {ready_batch}")
            
            # Record metrics for this wave
            for doc_id in ready_batch:
                metrics.record_document_start(doc_id)
            
            # Execute batch in parallel
            tasks = []
            for doc_id in ready_batch:
                tasks.append(self._generate_single_doc(
                    document_id=doc_id,
                    project_id=project_id,
                    user_idea=user_idea,
                    generated_docs=generated_docs,
                    progress_callback=progress_callback,
                    total=total,
                    completed_count=len(completed_docs)
                ))
            
            # Wait for all in batch to complete
            # We use return_exceptions=True to continue even if some fail
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            wave_duration = time.time() - wave_start_time
            
            for i, res in enumerate(batch_results):
                doc_id = ready_batch[i]
                if isinstance(res, Exception):
                    logger.error(f"Error generating {doc_id}: {res}")
                    # Record failure in metrics
                    metrics.record_document_complete(doc_id, success=False)
                    
                    # If a doc fails, we cannot generate its dependents.
                    # We remove it from pending but do NOT add to completed.
                    # This will naturally block dependents.
                    pending_docs.remove(doc_id)
                    
                    # Don't update project status here - wait until all waves complete
                    # to determine final status (complete, partial_failure, or failed)
                else:
                    # Success
                    d_id, d_result = res
                    generated_docs[d_id] = d_result
                    completed_docs.add(d_id)
                    pending_docs.remove(d_id)
                    
                    # Record success in metrics
                    metrics.record_document_complete(d_id, success=True)
                    
                    # Add to results
                    definition = self.definitions.get(d_id)
                    results["files"][d_id] = {
                        "content": d_result.get("content", ""),
                        "path": d_result.get("file_path", ""),
                        "file_path": d_result.get("file_path", ""),
                    }
                    
                    if definition:
                        results["documents"].append({
                            "id": d_id,
                    "name": definition.name,
                    "category": definition.category,
                            "file_path": d_result.get("file_path", ""),
                            "generated_at": d_result.get("generated_at"),
                    "dependencies": definition.dependencies,
                        })
                    
                    # Update status incrementally
            self.context_manager.update_project_status(
                project_id=project_id,
                status="in_progress",
                        user_idea=user_idea,
                        completed_agents=list(completed_docs),
                results=results,
                selected_documents=selected_documents,
            )

            # Calculate parallel efficiency after all documents in batch have completed
            # Sum up actual durations of successfully completed documents in this wave
            sequential_estimate = sum(
                metrics.document_times.get(doc_id, {}).get("duration", 0)
                for doc_id in ready_batch
                if doc_id in metrics.document_times and metrics.document_times[doc_id].get("duration") is not None
            )
            parallel_efficiency = (sequential_estimate / wave_duration * 100) if wave_duration > 0 and sequential_estimate > 0 else 0
            
            # Record wave metrics
            metrics.record_wave_execution(
                wave_number=wave_number,
                documents=ready_batch,
                execution_time=wave_duration,
                parallel_efficiency=parallel_efficiency
            )

        # Finalize
        workflow_duration = time.time() - workflow_start_time
        
        # Log metrics summary
        metrics.log_summary()
        
        # Determine final status based on completed vs failed documents
        total_completed = len(completed_docs)
        total_failed = metrics.failed_documents
        final_status = "complete"
        error_message = None
        
        if total_completed == 0 and total_failed > 0:
            # All documents failed
            final_status = "failed"
            error_message = f"All {total_failed} document(s) failed to generate"
        elif total_completed < total:
            # Some documents failed or were blocked by dependencies
            final_status = "partial_failure"
            if total_failed > 0:
                error_message = f"{total_failed} document(s) failed to generate. {total_completed}/{total} completed."
            else:
                error_message = f"{total_completed}/{total} documents completed"
        
        logger.info(f"🎉 Workflow completed in {workflow_duration:.2f}s. Generated {total_completed}/{total} docs. Failed: {total_failed}")

        results["summary"] = {
            "project_id": project_id,
            "generated_at": datetime.now().isoformat(),
            "total_documents": total_completed,
            "selected_documents": selected_documents,
            "metrics": metrics.get_summary(),  # Include metrics in results
        }
        
        self.context_manager.update_project_status(
            project_id=project_id,
            status=final_status,
            user_idea=user_idea,
            completed_agents=list(completed_docs),
            results=results,
            selected_documents=selected_documents,
            error=error_message
        )
        
        # Clean up metrics
        clear_metrics(project_id)
            
        return results

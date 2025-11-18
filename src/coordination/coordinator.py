"""Configuration-driven workflow coordinator for OmniDoc."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
import re
import asyncio
import time

from src.agents.generic_document_agent import GenericDocumentAgent
from src.agents.special_agent_adapter import SpecialAgentAdapter
from src.agents.special_agent_registry import get_special_agent_class
from src.agents.quality_reviewer_agent import QualityReviewerAgent
from src.agents.document_improver_agent import DocumentImproverAgent
from src.config.document_catalog import (
    DocumentDefinition,
    load_document_definitions,
    resolve_dependencies,
)
from src.config.settings import get_settings
from src.context.context_manager import ContextManager
from src.utils.logger import get_logger

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
            
            logger.info(
                "🔍 Reviewing quality of document %s [Project: %s] [Content length: %d chars]",
                document_id,
                project_id,
                len(original_content)
            )
            
            # Get automated quality scores first (to include llm_focus and auto_fail)
            from src.quality.document_type_quality_checker import DocumentTypeQualityChecker
            doc_type_checker = DocumentTypeQualityChecker()
            automated_scores = doc_type_checker.check_quality_for_type(
                content=original_content,
                document_type=document_name  # Use document name for better matching
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
            logger.info(
                "📊 Quality score for %s: %.1f/10 [Project: %s]",
                document_id,
                quality_score,
                project_id
            )
            
            # Step 2: Check if improvement is needed (threshold: 7.0/10)
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
                structured_feedback=structured_feedback_dict,
            )
            
            improvement_ratio = (len(merged_content) / len(original_content)) * 100 if original_content else 0
            logger.info(
                "✅ Document %s improved [Project: %s] [Original: %d chars] [Improved: %d chars] [Change: %.1f%%]",
                document_id,
                project_id,
                len(original_content),
                len(merged_content),
                improvement_ratio - 100
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
        2. Otherwise, identify sections that need improvement and merge them
        3. Preserve original sections that don't need changes
        """
        # If improved content is much longer and seems complete, use it
        if len(improved_content) > len(original_content) * 1.2:
            # Check if improved content contains key sections from original
            original_sections = self._extract_sections(original_content)
            improved_sections = self._extract_sections(improved_content)
            
            # If improved has all or most original sections, use it
            if len(improved_sections) >= len(original_sections) * 0.8:
                return improved_content
        
        # Otherwise, try to merge specific sections
        # For now, return improved content as document improver should preserve structure
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

    async def async_generate_all_docs(
        self,
        user_idea: str,
        project_id: str,
        selected_documents: List[str],
        codebase_path: Optional[str] = None,  # Reserved for future use
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Dict]:
        del codebase_path  # Currently unused; keep signature for future enhancements

        if not selected_documents:
            raise ValueError("No documents selected for generation.")

        try:
            execution_plan = resolve_dependencies(selected_documents)
        except ValueError as exc:
            logger.info("Dependency resolution issue: %s", exc)
            raise
        
        total = len(execution_plan)
        completed: List[str] = []
        generated_docs: Dict[str, Dict[str, str]] = {}
        results: Dict[str, Dict] = {"files": {}, "documents": []}

        workflow_start_time = time.time()
        logger.info(
            "🚀 Starting document generation workflow [Project: %s] [Total documents: %d] [Execution plan: %s] [User idea length: %d chars]",
            project_id,
            total,
            ", ".join(execution_plan),
            len(user_idea)
        )
        
        # Log user idea preview
        user_idea_preview = user_idea[:200] + "..." if len(user_idea) > 200 else user_idea
        logger.info(
            "💡 User idea preview [Project: %s]: %s",
            project_id,
            user_idea_preview
        )

        if progress_callback:
            await progress_callback(
                {
                    "type": "plan",
            "project_id": project_id,
                    "documents": ",".join(execution_plan),
                    "total": str(total),
                }
            )

        for index, document_id in enumerate(execution_plan, start=1):
            logger.info(
                "📄 Generating document %d/%d: %s [Project: %s]",
                index,
                total,
                document_id,
                project_id
            )
            # Also print to stderr for Railway visibility
            import sys
            print(f"[DOCUMENT GENERATION] Starting {document_id} ({index}/{total}) for project {project_id}", file=sys.stderr, flush=True)
            
            definition = self.definitions.get(document_id)
            if not definition:
                logger.error("Unknown document id '%s' in execution plan [Project: %s]", document_id, project_id)
                raise ValueError(f"Unknown document id '{document_id}' in execution plan.")

            agent = self.agents.get(document_id)
            if not agent:
                logger.error("No agent available for document '%s' [Project: %s]", document_id, project_id)
                raise ValueError(f"No agent available for document '{document_id}'.")

            # Build dependency payload from all dependencies (document_definitions.json + quality_rules.json)
            from src.config.document_catalog import get_all_dependencies
            
            all_dependencies = get_all_dependencies(document_id)
            dependency_payload = {
                dependency: generated_docs[dependency]
                for dependency in all_dependencies
                if dependency in generated_docs
            }
            
            # For documents that need context but have no explicit dependencies,
            # include commonly useful documents (project_charter, business_model, requirements)
            # This helps documents like GTM strategy that need context but don't have dependencies defined
            if not dependency_payload and document_id in ["gtm_strategy", "marketing_plan"]:
                # Include project_charter and business_model if available
                for useful_doc_id in ["project_charter", "business_model", "requirements"]:
                    if useful_doc_id in generated_docs:
                        dependency_payload[useful_doc_id] = generated_docs[useful_doc_id]
                        logger.debug(
                            "Including %s as context for %s (no explicit dependencies) [Project: %s]",
                            useful_doc_id,
                            document_id,
                            project_id
                        )
            
            logger.debug(
                "Document %s dependencies: %s (from definitions: %s, from quality_rules: %s) [Available: %s] [Project: %s]",
                document_id,
                all_dependencies,
                definition.dependencies,
                [d for d in all_dependencies if d not in definition.dependencies],
                list(dependency_payload.keys()),
                project_id
            )

            if progress_callback:
                await progress_callback(
                    {
                        "type": "document_started",
            "project_id": project_id,
                        "document_id": document_id,
                        "name": definition.name,
                        "index": str(index),
                        "total": str(total),
                    }
                )

            output_rel_path = f"{project_id}/{document_id}.md"
            
            # Update adapter's project_id if it's a SpecialAgentAdapter
            if isinstance(agent, SpecialAgentAdapter):
                agent.project_id = project_id
                agent.context_manager = self.context_manager
            
            doc_start_time = time.time()
            try:
                # Log detailed generation start information
                logger.info(
                    "📝 Starting generation for document: %s [Project: %s] [Dependencies: %s] [Agent: %s]",
                    document_id,
                    project_id,
                    list(dependency_payload.keys()),
                    type(agent).__name__
                )
                
                logger.info(f"🟣 Coordinator: About to call agent.generate_and_save for {document_id} (agent: {type(agent).__name__})")
                try:
                    document_result = await agent.generate_and_save(
                        user_idea=user_idea,
                        dependency_documents=dependency_payload,
                        output_rel_path=output_rel_path,
                        project_id=project_id,
                    )
                    doc_elapsed = time.time() - doc_start_time
                    logger.info(f"🟣 Coordinator: agent.generate_and_save completed for {document_id} in {doc_elapsed:.2f}s")
                except Exception as e:
                    doc_elapsed = time.time() - doc_start_time
                    logger.error(f"🟣 Coordinator: agent.generate_and_save FAILED for {document_id} after {doc_elapsed:.2f}s: {type(e).__name__}: {str(e)}", exc_info=True)
                    raise
                doc_duration = time.time() - doc_start_time
                content = document_result.get("content", "")
                content_length = len(content)
                quality_score = document_result.get("quality_score")
                file_path = document_result.get("file_path", "")
                
                # Log comprehensive generation results
                logger.info(
                    "✅ Document %s generated successfully [Project: %s] [Duration: %.2fs] [Size: %d chars] [Quality: %s] [Path: %s]",
                    document_id,
                    project_id,
                    doc_duration,
                    content_length,
                    f"{quality_score:.1f}/10" if quality_score else "N/A",
                    file_path
                )
                
                # Log document statistics (simplified)
                word_count = len(content.split()) if content else 0
                logger.debug(
                    "Document %s: %d words, %d chars [Project: %s]",
                    document_id,
                    word_count,
                    content_length,
                    project_id
                )
                
                # Also print to stderr for Railway visibility
                print(f"[DOCUMENT GENERATION] ✅ Completed {document_id} ({index}/{total}) in {doc_duration:.2f}s ({content_length} chars) for project {project_id}", file=sys.stderr, flush=True)
            except Exception as e:
                doc_duration = time.time() - doc_start_time
                logger.error(
                    "Failed to generate document %s after %.2fs [Project: %s] [Error: %s]",
                    document_id,
                    doc_duration,
                    project_id,
                    str(e),
                    exc_info=True
                )
                raise

            # Quality review and improvement workflow
            original_content = document_result.get("content", "")
            if original_content:
                review_start_time = time.time()
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
                review_duration = time.time() - review_start_time
                if improved_content and improved_content != original_content:
                    logger.info(
                        "✅ Document %s improved [Original: %d chars → Improved: %d chars] [Duration: %.2fs] [Project: %s]",
                        document_id,
                        len(original_content),
                        len(improved_content),
                        review_duration,
                        project_id
                    )
                else:
                    logger.debug(
                        "Document %s passed quality review without changes [Duration: %.2fs] [Project: %s]",
                        document_id,
                        review_duration,
                        project_id
                    )
                
                # Update document result with improved content
                if improved_content and improved_content != original_content:
                    document_result["content"] = improved_content
                    # Update content in database (not in file)
                    # Save improved content to database
                    try:
                        from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
                        # Try to determine agent_type from document_id
                        agent_type = None
                        try:
                            agent_type = AgentType(document_id)
                        except ValueError:
                            # Not a standard AgentType - use fallback
                            logger.debug(f"Document {document_id} not in AgentType enum, using TECHNICAL_DOCUMENTATION fallback")
                            try:
                                agent_type = AgentType.TECHNICAL_DOCUMENTATION  # Generic fallback
                            except:
                                agent_type = list(AgentType)[0]  # Last resort
                        
                        # Always save to database - document_type identifies the actual document
                        output = AgentOutput(
                            agent_type=agent_type,
                            document_type=document_id,  # This is the key identifier
                            content=improved_content,
                            file_path=document_result.get("file_path"),  # Virtual path
                            status=DocumentStatus.COMPLETE,
                            quality_score=document_result.get("quality_score"),
                        )
                        self.context_manager.save_agent_output(project_id, output)
                        logger.info(f"✅ Document {document_id} improved and updated in database [agent_type: {agent_type.value}, document_type: {document_id}]")
                    except Exception as e:
                        logger.error(f"❌ Could not update improved document {document_id} in database: {e}", exc_info=True)

            generated_docs[document_id] = document_result
            completed.append(document_id)

            # Store document info as dictionary (not just file_path string) for statistics
            results["files"][document_id] = {
                "content": document_result.get("content", ""),
                "path": document_result.get("file_path", ""),
                "file_path": document_result.get("file_path", ""),
            }
            results["documents"].append(
                {
                    "id": document_id,
                    "name": definition.name,
                    "category": definition.category,
                    "file_path": document_result["file_path"],
                    "generated_at": document_result["generated_at"],
                    "dependencies": definition.dependencies,
                }
            )

            logger.info(
                "Document %s saved and status updated [Progress: %d/%d] [Project: %s]",
                document_id,
                len(completed),
                total,
                project_id
            )

            self.context_manager.update_project_status(
                project_id=project_id,
                status="in_progress",
                user_idea=user_idea,  # Include user_idea in case status doesn't exist yet
                completed_agents=completed,
                results=results,
                selected_documents=selected_documents,
            )

            if progress_callback:
                await progress_callback(
                    {
                        "type": "document_completed",
                        "project_id": project_id,
                        "document_id": document_id,
                        "name": definition.name,
                        "index": str(index),
                        "total": str(total),
                    }
                )

        results["summary"] = {
            "project_id": project_id,
            "generated_at": datetime.now().isoformat(),
            "total_documents": len(completed),
            "selected_documents": selected_documents,
        }

        workflow_duration = time.time() - workflow_start_time
        total_chars = sum(len(doc.get("content", "")) for doc in generated_docs.values())
        total_words = sum(len(doc.get("content", "").split()) for doc in generated_docs.values())
        
        logger.info(
            "🎉 Document generation workflow completed [Project: %s] [Total: %d documents] [Generated: %d] [Duration: %.2fs] [Total content: %d chars, %d words]",
            project_id,
            total,
            len(completed),
            workflow_duration,
            total_chars,
            total_words
        )
        
        # Log summary of all generated documents
        logger.info(
            "📋 Generation summary [Project: %s]:",
            project_id
        )
        for doc_id, doc_data in generated_docs.items():
            content_len = len(doc_data.get("content", ""))
            quality = doc_data.get("quality_score", "N/A")
            logger.info(
                "  - %s: %d chars, quality: %s",
                doc_id,
                content_len,
                f"{quality:.1f}/10" if isinstance(quality, (int, float)) else quality
            )

        self.context_manager.update_project_status(
            project_id=project_id,
            status="complete",
            user_idea=user_idea,  # Include user_idea for consistency
            completed_agents=completed,
            results=results,
            selected_documents=selected_documents,
        )
            
        return results


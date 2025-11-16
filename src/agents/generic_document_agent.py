"""Agent for configuration-driven document generation."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from prompts.system_prompts import READABILITY_GUIDELINES
from src.agents.base_agent import BaseAgent
from src.config.document_catalog import DocumentDefinition
from src.context.context_manager import ContextManager
from src.utils.file_manager import FileManager
from src.utils.logger import get_logger
from src.utils.prompt_registry import get_prompt_for_document

logger = get_logger(__name__)


class GenericDocumentAgent(BaseAgent):
    """Generic prompt-driven document generator using catalog metadata."""

    def __init__(
        self,
        definition: DocumentDefinition,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        base_output_dir: str = "docs/generated",
        context_manager: Optional[ContextManager] = None,
        **provider_kwargs,
    ) -> None:
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            **provider_kwargs,
        )
        self.definition = definition
        self.output_filename = f"{definition.id}.md"
        self.file_manager = FileManager(base_dir=base_output_dir)
        self.context_manager = context_manager
        self.project_id: Optional[str] = None

    def _get_project_context(self, project_id: Optional[str]) -> Dict:
        """Get project context from ContextManager if available"""
        context = {}
        
        if not project_id or not self.context_manager:
            return context
        
        try:
            # Get parsed requirements if available
            requirements = self.context_manager.get_requirements(project_id)
            if requirements:
                # RequirementsDocument is a dataclass, access attributes directly
                context["requirements"] = {
                    "project_overview": requirements.project_overview or "",
                    "core_features": requirements.core_features or [],
                    "business_objectives": requirements.business_objectives or [],
                    "user_personas": requirements.user_personas or [],
                    "technical_requirements": requirements.technical_requirements or {},
                    "constraints": requirements.constraints or [],
                }
                logger.debug(f"Retrieved requirements context for project {project_id}")
            
            # Get other agent outputs that might be relevant
            # (This could be expanded to get specific document types)
            
        except Exception as e:
            logger.warning(f"Could not retrieve project context: {e}", exc_info=True)
        
        return context
    
    def _build_prompt(
        self,
        user_idea: str,
        dependency_documents: Dict[str, Dict[str, str]],
        project_id: Optional[str] = None,
    ) -> str:
        # Get project context from ContextManager
        project_context = self._get_project_context(project_id)
        
        logger.debug(
            "Building prompt for document %s [Project: %s] [Dependencies: %d] [Has context: %s]",
            self.definition.id,
            project_id or "N/A",
            len(dependency_documents),
            bool(project_context.get("requirements"))
        )
        
        # Try to get a specialized prompt from the registry
        specialized_prompt = get_prompt_for_document(
            document_id=self.definition.id,
            user_idea=user_idea,
            dependency_documents=dependency_documents,
        )

        if specialized_prompt:
            logger.debug(
                "Using specialized prompt for document %s [Prompt length: %d chars] [Project: %s]",
                self.definition.id,
                len(specialized_prompt),
                project_id or "N/A"
            )
            # Specialized prompts already include user_idea and dependencies via prompt_registry
            # But we can still add project context if available for additional enrichment
            if project_context.get("requirements"):
                context_section = "\n\n### Additional Project Context (from Requirements Analysis):\n"
                req = project_context["requirements"]
                if req.get("project_overview"):
                    context_section += f"**Project Overview:** {req['project_overview']}\n\n"
                if req.get("core_features"):
                    context_section += "**Core Features:**\n" + "\n".join(f"- {f}" for f in req["core_features"]) + "\n\n"
                if req.get("business_objectives"):
                    context_section += "**Business Objectives:**\n" + "\n".join(f"- {obj}" for obj in req["business_objectives"]) + "\n\n"
                specialized_prompt += context_section
            
            # Ensure dependency documents are mentioned if they exist
            if dependency_documents:
                deps_section = "\n\n### Available Dependency Documents:\n"
                deps_section += "The following dependency documents are available for reference:\n"
                for dep_id, dep_data in dependency_documents.items():
                    deps_section += f"- **{dep_data.get('name', dep_id)}** ({dep_id})\n"
                deps_section += "\nThese documents have been provided in the context above. Use them to ensure consistency and build upon existing information.\n"
                specialized_prompt += deps_section
            
            return specialized_prompt

        # Fall back to generic template
        logger.debug("Using generic prompt template for document %s", self.definition.id)
        description = self.definition.description or "Generate the requested project documentation."
        guidance = [
            f"You are responsible for producing the document '{self.definition.name}'.",
            f"Document ID: {self.definition.id}",
            f"Category: {self.definition.category or 'General'}",
            f"Priority: {self.definition.priority or 'Unspecified'}",
            "",
            "### Project Idea",
            user_idea.strip(),
            "",
            "### Document Description",
            description,
        ]

        # Add project context if available
        if project_context.get("requirements"):
            req = project_context["requirements"]
            guidance.extend(["", "### Project Context (from Requirements Analysis)"])
            if req.get("project_overview"):
                guidance.append(f"**Project Overview:** {req['project_overview']}")
            if req.get("core_features"):
                guidance.append("**Core Features:**")
                guidance.extend([f"- {f}" for f in req["core_features"]])
            if req.get("business_objectives"):
                guidance.append("**Business Objectives:**")
                guidance.extend([f"- {obj}" for obj in req["business_objectives"]])
            if req.get("technical_requirements"):
                guidance.append("**Technical Requirements:**")
                if isinstance(req["technical_requirements"], dict):
                    for key, value in req["technical_requirements"].items():
                        guidance.append(f"- {key}: {value}")
                else:
                    guidance.append(f"- {req['technical_requirements']}")
            if req.get("constraints"):
                guidance.append("**Constraints:**")
                guidance.extend([f"- {c}" for c in req["constraints"]])
            guidance.append("")  # Empty line

        if self.definition.notes:
            guidance.extend(["", "### Additional Notes", self.definition.notes])

        if dependency_documents:
            guidance.extend(["", "### Reference Materials (Dependency Documents)"])
            guidance.append("The following documents have been generated and should be used as reference:")
            for dep_id, dep_data in dependency_documents.items():
                excerpt = dep_data.get("content", "").strip()
                if not excerpt:
                    continue
                # Include more content for better context (up to 8000 chars per document)
                excerpt = excerpt[:8000]
                if len(dep_data.get("content", "")) > 8000:
                    excerpt += f"\n[... document continues, {len(dep_data.get('content', ''))} total characters ...]"
                guidance.extend(
                    [
                        f"#### {dep_data.get('name', dep_id)} ({dep_id})",
                        excerpt,
                        "",
                    ]
                )
            guidance.append("CRITICAL: Use the information from these dependency documents to ensure consistency and accuracy. Reference specific details, align with existing plans, and build upon the foundation established in these documents.")

        guidance.extend(
            [
                "### Requirements",
                "- Produce a comprehensive Markdown document tailored to the project idea.",
                "- Use clear headings, subheadings, bullet lists, and tables when appropriate.",
                "- Incorporate relevant details from the reference materials.",
                "- Provide actionable recommendations, plans, or specifications as appropriate.",
                "- Ensure the content is original; do not copy source text verbatim unless quoting.",
                "",
                "🚨 CRITICAL COMPLETENESS REQUIREMENTS:",
                "- You MUST complete ALL sections with full, detailed content - do not leave any section incomplete",
                "- You MUST NOT use placeholder text like '[Describe...]', '[Example:...]', or '[Estimate...]'",
                "- You MUST fill in ALL tables completely with actual data, not placeholders",
                "- You MUST generate specific, actionable content based on the project information provided",
                "- You MUST ensure the document is comprehensive and complete - do not stop mid-section",
                "- If a section requires examples, provide real, specific examples based on the project",
                "- If a section requires data or metrics, provide realistic estimates based on the project scope",
                "",
                READABILITY_GUIDELINES.strip(),
                "",
                "Begin the document now. Generate the COMPLETE document with ALL sections fully populated:",
            ]
        )

        return "\n".join(guidance)

    def generate(
        self,
        user_idea: str,
        dependency_documents: Dict[str, Dict[str, str]],
        project_id: Optional[str] = None,
    ) -> str:
        prompt = self._build_prompt(user_idea, dependency_documents, project_id)
        return self._call_llm(prompt, temperature=self.default_temperature)

    async def async_generate(
        self,
        user_idea: str,
        dependency_documents: Dict[str, Dict[str, str]],
        project_id: Optional[str] = None,
    ) -> str:
        prompt = self._build_prompt(user_idea, dependency_documents, project_id)
        return await self._async_call_llm(prompt, temperature=self.default_temperature)

    async def generate_and_save(
        self,
        user_idea: str,
        dependency_documents: Dict[str, Dict[str, str]],
        output_rel_path: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, str]:
        # Store project_id for context retrieval
        if project_id:
            self.project_id = project_id
        
        logger.debug(
            "Generating document: %s [Project: %s] [Dependencies: %d] [Output: %s]",
            self.definition.id,
            project_id or "N/A",
            len(dependency_documents),
            output_rel_path
        )
        
        try:
            content = await self.async_generate(user_idea, dependency_documents, project_id)
            logger.debug(
                "Document %s generated [Size: %d chars] [Project: %s]",
                self.definition.id,
                len(content),
                project_id or "N/A"
            )
        except Exception as exc:
            logger.error(
                "Failed to generate document %s [Project: %s] [Error: %s]",
                self.definition.id,
                project_id or "N/A",
                str(exc),
                exc_info=True
            )
            raise

        # Generate virtual file path for reference (not used for actual file storage)
        virtual_path = f"docs/{output_rel_path}"
        logger.debug(
            "Document %s saving to database (virtual path: %s) [Project: %s]",
            self.definition.id,
            virtual_path,
            project_id or "N/A"
        )
        
        # Save to database if context_manager is available
        if project_id and self.context_manager:
            try:
                from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
                # Try to map document_id to AgentType
                agent_type = None
                try:
                    agent_type = AgentType(self.definition.id)
                except ValueError:
                    # Not a standard AgentType - use GENERIC_DOCUMENT as fallback
                    # This allows us to save any document type to the database
                    logger.debug(f"Document {self.definition.id} not in AgentType enum, using GENERIC_DOCUMENT fallback")
                    # Use a generic agent type that exists in the enum
                    # We'll use document_type to identify the actual document
                    try:
                        # Try to use a generic type that makes sense
                        agent_type = AgentType.TECHNICAL_DOCUMENTATION  # Generic fallback
                    except:
                        # Last resort - use any available type
                        agent_type = list(AgentType)[0]  # Use first available type
                
                # Always save to database - document_type identifies the actual document
                output = AgentOutput(
                    agent_type=agent_type,
                    document_type=self.definition.id,  # This is the key identifier
                    content=content,
                    file_path=virtual_path,  # Virtual path for reference only
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                self.context_manager.save_agent_output(project_id, output)
                logger.info(f"✅ Document {self.definition.id} saved to database [agent_type: {agent_type.value}, document_type: {self.definition.id}]")
            except Exception as e:
                logger.error(f"❌ Could not save document {self.definition.id} to database: {e}", exc_info=True)
        
        return {
            "id": self.definition.id,
            "name": self.definition.name,
            "file_path": virtual_path,  # Virtual path for reference only
            "content": content,
            "generated_at": datetime.now().isoformat(),
        }


"""Adapter to make special agents compatible with GenericDocumentAgent interface."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.agents.base_agent import BaseAgent
from src.agents.requirements_analyst import RequirementsAnalyst
from src.config.document_catalog import DocumentDefinition
from src.context.context_manager import ContextManager
from src.utils.file_manager import FileManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SpecialAgentAdapter:
    """Adapter to make special agents work with the coordinator's expected interface."""

    def __init__(
        self,
        agent: BaseAgent,
        definition: DocumentDefinition,
        base_output_dir: str,
        context_manager: Optional[ContextManager] = None,
        project_id: Optional[str] = None,
    ) -> None:
        self.agent = agent
        self.definition = definition
        self.file_manager = FileManager(base_dir=base_output_dir)
        self.context_manager = context_manager
        self.project_id = project_id

    async def async_generate(
        self,
        user_idea: str,
        dependency_documents: Dict[str, Dict[str, str]],
    ) -> str:
        """Generate document content asynchronously."""
        # For most special agents, we can use the sync generate in an executor
        # RequirementsAnalyst has special handling
        if isinstance(self.agent, RequirementsAnalyst):
            # RequirementsAnalyst.generate only takes user_idea
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.agent.generate, user_idea)

        # For other special agents, try to call generate with user_idea
        # Most special agents have different signatures, so we'll need to adapt
        if hasattr(self.agent, "generate"):
            import asyncio

            loop = asyncio.get_event_loop()
            # Try calling with just user_idea first
            try:
                return await loop.run_in_executor(None, self.agent.generate, user_idea)
            except TypeError:
                # If that fails, try with dependency_documents
                logger.warning(
                    "Special agent %s may not support dependency_documents, using user_idea only",
                    type(self.agent).__name__,
                )
                return await loop.run_in_executor(None, self.agent.generate, user_idea)

        raise NotImplementedError(f"Agent {type(self.agent).__name__} does not have a generate method")

    async def generate_and_save(
        self,
        user_idea: str,
        dependency_documents: Dict[str, Dict[str, str]],
        output_rel_path: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate and save document, returning metadata dict compatible with GenericDocumentAgent."""
        try:
            content = await self.async_generate(user_idea, dependency_documents)
        except Exception as exc:
            logger.error("Failed to generate document %s: %s", self.definition.id, exc, exc_info=True)
            raise

        # Generate virtual file path for reference (not used for actual file storage)
        virtual_path = f"docs/{output_rel_path}"

        # Update project_id if provided
        if project_id:
            self.project_id = project_id
        
        # Save to database via context_manager
        if self.context_manager and self.project_id:
            try:
                from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
                
                # Determine agent type from definition
                agent_type = AgentType.REQUIREMENTS_ANALYST if isinstance(self.agent, RequirementsAnalyst) else None
                
                if agent_type:
                    output = AgentOutput(
                        agent_type=agent_type,
                        document_type=self.definition.id,
                        content=content,
                        file_path=virtual_path,  # Virtual path for reference only
                        status=DocumentStatus.COMPLETE,
                    )
                    self.context_manager.save_agent_output(self.project_id, output)
                    logger.info(f"✅ Document {self.definition.id} saved to database")

                # Also parse and save requirements if possible
                if isinstance(self.agent, RequirementsAnalyst) and hasattr(self.agent, "parser") and hasattr(self.agent, "_save_to_context"):
                    # Create a temporary RequirementsDocument-like object
                    # The agent's _save_to_context will handle parsing
                    self.agent.project_id = self.project_id
                    self.agent.context_manager = self.context_manager
                    self.agent._save_to_context(content, virtual_path, user_idea)
            except Exception as exc:
                logger.warning("Failed to save to database: %s", exc)

        return {
            "id": self.definition.id,
            "name": self.definition.name,
            "file_path": virtual_path,
            "content": content,
            "generated_at": datetime.now().isoformat(),
        }


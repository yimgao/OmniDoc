"""Registry for special-case agents that require custom logic."""
from __future__ import annotations

from typing import Dict, Optional, Type

from src.agents.base_agent import BaseAgent
from src.agents.code_analyst_agent import CodeAnalystAgent
from src.agents.document_improver_agent import DocumentImproverAgent
from src.agents.format_converter_agent import FormatConverterAgent
from src.agents.quality_reviewer_agent import QualityReviewerAgent
from src.agents.requirements_analyst import RequirementsAnalyst
from src.agents.marketing_plan_agent import MarketingPlanAgent
from src.agents.feature_roadmap_agent import FeatureRoadmapAgent
from src.agents.risk_management_agent import RiskManagementAgent

# Map document IDs to special agent classes
SPECIAL_AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "requirements": RequirementsAnalyst,
    "quality_review": QualityReviewerAgent,
    "document_improver": DocumentImproverAgent,
    "format_converter": FormatConverterAgent,
    "code_analyst": CodeAnalystAgent,
    "gtm_strategy": MarketingPlanAgent,
    "marketing_plan": MarketingPlanAgent,
    "feature_roadmap": FeatureRoadmapAgent,
    "risk_management_plan": RiskManagementAgent,
}

# Map special_key (from config) to document IDs
SPECIAL_KEY_TO_DOC_ID: Dict[str, str] = {
    "requirements_analyst": "requirements",
    "quality_reviewer": "quality_review",
    "document_improver": "document_improver",
    "format_converter": "format_converter",
    "code_analyst": "code_analyst",
    "marketing_plan": "marketing_plan",
    "feature_roadmap": "feature_roadmap",
    "risk_management_plan": "risk_management_plan",
}


def get_special_agent_class(document_id: str, special_key: Optional[str] = None) -> Optional[Type[BaseAgent]]:
    """Get special agent class for a document ID or special_key."""
    # First try direct document_id lookup
    agent_class = SPECIAL_AGENT_REGISTRY.get(document_id)
    if agent_class:
        return agent_class

    # Then try special_key lookup
    if special_key:
        mapped_doc_id = SPECIAL_KEY_TO_DOC_ID.get(special_key)
        if mapped_doc_id:
            return SPECIAL_AGENT_REGISTRY.get(mapped_doc_id)

    return None


def is_special_agent(document_id: str, special_key: Optional[str] = None) -> bool:
    """Check if a document ID requires a special agent."""
    return get_special_agent_class(document_id, special_key) is not None


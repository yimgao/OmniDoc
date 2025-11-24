"""Registry mapping document IDs to specialized prompt functions."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from prompts import system_prompts


def _extract_requirements_summary(
    user_idea: str,
    dependency_documents: Dict[str, Dict[str, str]],
) -> Dict[str, Any]:
    """Extract requirements summary from dependencies or build from user_idea."""
    summary: Dict[str, Any] = {"user_idea": user_idea}

    # Try to get requirements document
    req_doc = dependency_documents.get("requirements")
    if req_doc:
        content = req_doc.get("content", "")
        summary["requirements_document"] = content
        # Try to parse structured fields if available
        # For now, just include the full document
    else:
        summary["requirements_document"] = ""

    # Extract other common dependencies - check all possible document IDs
    # Project Charter
    project_charter = (
        dependency_documents.get("project_charter") or
        dependency_documents.get("project_charter_doc")
    )
    if project_charter:
        summary["project_charter_summary"] = project_charter.get("content", "")

    # Technical Documentation
    technical_doc = (
        dependency_documents.get("technical_documentation") or
        dependency_documents.get("tad") or
        dependency_documents.get("technical_architecture_doc")
    )
    if technical_doc:
        summary["technical_summary"] = technical_doc.get("content", "")

    # API Documentation
    api_doc = (
        dependency_documents.get("api_documentation") or
        dependency_documents.get("api_doc")
    )
    if api_doc:
        summary["api_summary"] = api_doc.get("content", "")

    # PM Documentation
    pm_doc = (
        dependency_documents.get("pm_documentation") or
        dependency_documents.get("pm_management_doc") or
        dependency_documents.get("pm_doc")
    )
    if pm_doc:
        summary["pm_summary"] = pm_doc.get("content", "")

    # User Stories
    user_stories_doc = (
        dependency_documents.get("user_stories") or
        dependency_documents.get("user_stories_doc")
    )
    if user_stories_doc:
        summary["user_stories"] = user_stories_doc.get("content", "")

    # Business Model
    business_model_doc = (
        dependency_documents.get("business_model") or
        dependency_documents.get("business_model_doc")
    )
    if business_model_doc:
        summary["business_model"] = business_model_doc.get("content", "")

    # Brick-and-Mortar documents
    business_overview_doc = dependency_documents.get("business_overview")
    if business_overview_doc:
        summary["business_overview_summary"] = business_overview_doc.get("content", "")

    operations_plan_doc = dependency_documents.get("operations_plan")
    if operations_plan_doc:
        summary["operations_plan_summary"] = operations_plan_doc.get("content", "")

    market_research_doc = dependency_documents.get("market_research")
    if market_research_doc:
        summary["market_research_summary"] = market_research_doc.get("content", "")

    financial_model_doc = dependency_documents.get("financial_model")
    if financial_model_doc:
        summary["financial_model_summary"] = financial_model_doc.get("content", "")

    licensing_checklist_doc = dependency_documents.get("licensing_checklist")
    if licensing_checklist_doc:
        summary["licensing_checklist_summary"] = licensing_checklist_doc.get("content", "")

    sop_doc = dependency_documents.get("sop")
    if sop_doc:
        summary["sop_summary"] = sop_doc.get("content", "")

    # WBS
    wbs_doc = dependency_documents.get("wbs")
    if wbs_doc:
        summary["wbs_summary"] = wbs_doc.get("content", "")

    # Database Schema
    db_schema_doc = (
        dependency_documents.get("database_schema") or
        dependency_documents.get("db_schema")
    )
    if db_schema_doc:
        summary["database_schema_summary"] = db_schema_doc.get("content", "")

    # Include ALL dependency documents for comprehensive context
    # This ensures specialized prompts can access any dependency they need
    summary["all_dependencies"] = dependency_documents

    return summary


def _get_prompt_for_document(
    document_id: str,
    user_idea: str,
    dependency_documents: Dict[str, Dict[str, str]],
) -> Optional[str]:
    """Get specialized prompt for a document ID, or None if not available."""
    req_summary = _extract_requirements_summary(user_idea, dependency_documents)

    # Map document IDs to prompt functions
    prompt_map: Dict[str, Callable] = {
        "requirements": lambda: system_prompts.get_requirements_prompt(user_idea),
        "project_charter": lambda: system_prompts.get_project_charter_prompt(req_summary),
        "user_stories": lambda: system_prompts.get_user_stories_prompt(
            req_summary, req_summary.get("project_charter_summary")
        ),
        "pm_documentation": lambda: system_prompts.get_pm_prompt(
            req_summary, req_summary.get("project_charter_summary")
        ),
        "pm_management_doc": lambda: system_prompts.get_pm_prompt(
            req_summary, req_summary.get("project_charter_summary")
        ),
        "wbs": lambda: system_prompts.get_wbs_prompt(
            req_summary, req_summary.get("project_charter_summary"), req_summary.get("pm_summary")
        ),
        "technical_documentation": lambda: system_prompts.get_technical_prompt(
            req_summary, req_summary.get("project_charter_summary"), req_summary.get("user_stories")
        ),
        "tad": lambda: system_prompts.get_technical_prompt(
            req_summary, req_summary.get("project_charter_summary"), req_summary.get("user_stories")
        ),
        "api_documentation": lambda: system_prompts.get_api_prompt(
            req_summary, req_summary.get("technical_summary")
        ),
        "database_schema": lambda: system_prompts.get_database_schema_prompt(
            req_summary, req_summary.get("technical_summary")
        ),
        "developer_guide": lambda: system_prompts.get_developer_prompt(
            req_summary, req_summary.get("technical_summary"), req_summary.get("api_summary")
        ),
        "developer_documentation": lambda: system_prompts.get_developer_prompt(
            req_summary, req_summary.get("technical_summary"), req_summary.get("api_summary")
        ),
        "setup_guide": lambda: system_prompts.get_setup_guide_prompt(
            req_summary, req_summary.get("technical_summary"), req_summary.get("api_summary")
        ),
        "user_documentation": lambda: system_prompts.get_user_prompt(req_summary),
        "test_documentation": lambda: system_prompts.get_test_prompt(
            req_summary, req_summary.get("technical_summary"), req_summary.get("api_summary")
        ),
        "test_plan": lambda: system_prompts.get_test_prompt(
            req_summary, req_summary.get("technical_summary"), req_summary.get("api_summary")
        ),
        "stakeholder_communication": lambda: system_prompts.get_stakeholder_prompt(
            req_summary, req_summary.get("pm_summary")
        ),
        "stakeholders_doc": lambda: system_prompts.get_stakeholder_prompt(
            req_summary, req_summary.get("pm_summary")
        ),
        "business_model": lambda: system_prompts.get_business_model_prompt(
            req_summary, req_summary.get("project_charter_summary")
        ),
        "marketing_plan": lambda: system_prompts.get_marketing_plan_prompt(
            req_summary,
            req_summary.get("project_charter_summary"),
            req_summary.get("business_model"),
        ),
        "gtm_strategy": lambda: system_prompts.get_marketing_plan_prompt(
            req_summary,
            req_summary.get("project_charter_summary"),
            req_summary.get("business_model"),
        ),
        "feature_roadmap": lambda: system_prompts.get_feature_roadmap_prompt(
            req_summary,
            req_summary.get("project_charter_summary"),
            req_summary.get("business_model"),
        ),
        "risk_management_plan": lambda: system_prompts.get_risk_management_prompt(
            req_summary,
            req_summary.get("project_charter_summary"),
            req_summary.get("business_model"),
        ),
        "support_playbook": lambda: system_prompts.get_support_playbook_prompt(req_summary),
        "legal_compliance": lambda: system_prompts.get_legal_compliance_prompt(req_summary),
        # Brick-and-Mortar documents
        "business_overview": lambda: system_prompts.get_business_overview_prompt(
            req_summary,
            req_summary.get("market_research_summary"),
        ),
        "operations_plan": lambda: system_prompts.get_operations_plan_prompt(
            req_summary,
            req_summary.get("business_overview_summary"),
        ),
        "market_research": lambda: system_prompts.get_market_research_prompt(req_summary),
        "financial_model": lambda: system_prompts.get_financial_model_prompt(
            req_summary,
            req_summary.get("business_overview_summary"),
            req_summary.get("operations_plan_summary"),
        ),
        "licensing_checklist": lambda: system_prompts.get_licensing_checklist_prompt(
            req_summary,
            req_summary.get("business_overview_summary"),
        ),
        "sop": lambda: system_prompts.get_sop_prompt(
            req_summary,
            req_summary.get("operations_plan_summary"),
        ),
        "hr_staffing_guide": lambda: system_prompts.get_hr_staffing_guide_prompt(
            req_summary,
            req_summary.get("operations_plan_summary"),
        ),
        "marketing_plan": lambda: system_prompts.get_marketing_branding_plan_prompt(
            req_summary,
            req_summary.get("business_overview_summary"),
            req_summary.get("market_research_summary"),
        ),
        "risk_management_plan": lambda: system_prompts.get_risk_management_plan_prompt(
            req_summary,
            req_summary.get("business_overview_summary"),
            req_summary.get("operations_plan_summary"),
            req_summary.get("financial_model_summary"),
        ),
        "customer_experience_playbook": lambda: system_prompts.get_customer_experience_playbook_prompt(
            req_summary,
            req_summary.get("sop_summary"),
            req_summary.get("operations_plan_summary"),
        ),
        "growth_expansion_plan": lambda: system_prompts.get_growth_expansion_plan_prompt(
            req_summary,
            req_summary.get("business_overview_summary"),
            req_summary.get("financial_model_summary"),
        ),
        "execution_roadmap": lambda: system_prompts.get_execution_roadmap_prompt(
            req_summary,
            req_summary.get("licensing_checklist_summary"),
            req_summary.get("operations_plan_summary"),
            req_summary.get("marketing_plan_summary") or req_summary.get("marketing_plan"),
        ),
    }

    prompt_fn = prompt_map.get(document_id)
    if not prompt_fn:
        return None

    try:
        return prompt_fn()
    except Exception as exc:
        # Log error but don't fail - fall back to generic prompt
        from src.utils.logger import get_logger

        logger = get_logger(__name__)
        logger.warning("Failed to generate specialized prompt for %s: %s", document_id, exc)
        return None


def get_prompt_for_document(
    document_id: str,
    user_idea: str,
    dependency_documents: Dict[str, Dict[str, str]],
) -> Optional[str]:
    """Public interface to get specialized prompt for a document."""
    return _get_prompt_for_document(document_id, user_idea, dependency_documents)


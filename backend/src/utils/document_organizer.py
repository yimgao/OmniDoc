"""
Document Organizer
Organizes documents by level (Level 1: Strategic, Level 2: Product, Level 3: Technical)
"""
from typing import Dict, List, Tuple, Optional
from enum import Enum


class DocumentLevel(str, Enum):
    """Document levels"""
    LEVEL_1_STRATEGIC = "Level 1: Strategic (Entrepreneur)"
    LEVEL_2_PRODUCT = "Level 2: Product (Product Manager)"
    LEVEL_3_TECHNICAL = "Level 3: Technical (Programmer)"
    CROSS_LEVEL = "Cross-Level (Everyone)"


# Mapping from document types to levels
DOCUMENT_LEVEL_MAPPING = {
    # Level 1: Strategic (Entrepreneur)
    "requirements": DocumentLevel.LEVEL_1_STRATEGIC,
    "requirements_analyst": DocumentLevel.LEVEL_1_STRATEGIC,
    "stakeholder_documentation": DocumentLevel.LEVEL_1_STRATEGIC,
    "stakeholder_communication": DocumentLevel.LEVEL_1_STRATEGIC,
    "project_charter": DocumentLevel.LEVEL_1_STRATEGIC,
    "business_model": DocumentLevel.LEVEL_1_STRATEGIC,
    "marketing_plan": DocumentLevel.LEVEL_1_STRATEGIC,
    
    # Level 2: Product (Product Manager)
    "pm_documentation": DocumentLevel.LEVEL_2_PRODUCT,
    "user_stories": DocumentLevel.LEVEL_2_PRODUCT,
    "wbs_agent": DocumentLevel.LEVEL_2_PRODUCT,
    "work_breakdown_structure": DocumentLevel.LEVEL_2_PRODUCT,
    
    # Level 3: Technical (Programmer)
    "technical_documentation": DocumentLevel.LEVEL_3_TECHNICAL,
    "api_documentation": DocumentLevel.LEVEL_3_TECHNICAL,
    "database_schema": DocumentLevel.LEVEL_3_TECHNICAL,
    "setup_guide": DocumentLevel.LEVEL_3_TECHNICAL,
    "legal_compliance": DocumentLevel.LEVEL_3_TECHNICAL,
    
    # Cross-Level (Everyone)
    "developer_documentation": DocumentLevel.CROSS_LEVEL,
    "user_documentation": DocumentLevel.CROSS_LEVEL,
    "test_documentation": DocumentLevel.CROSS_LEVEL,
    "support_playbook": DocumentLevel.CROSS_LEVEL,
    "quality_reviewer": DocumentLevel.CROSS_LEVEL,
    "format_converter": DocumentLevel.CROSS_LEVEL,
    "claude_cli_documentation": DocumentLevel.CROSS_LEVEL,
}

# Human-readable names for document types
DOCUMENT_DISPLAY_NAMES = {
    "requirements": "Requirements Document",
    "requirements_analyst": "Requirements Document",
    "project_charter": "Project Charter (Business Case)",
    "stakeholder_documentation": "Stakeholder Summary",
    "stakeholder_communication": "Stakeholder Summary",
    "pm_documentation": "Project Management Plan",
    "user_stories": "User Stories & Epics",
    "wbs_agent": "Work Breakdown Structure",
    "work_breakdown_structure": "Work Breakdown Structure",
    "technical_documentation": "Technical Specification",
    "api_documentation": "API Documentation",
    "database_schema": "Database Schema",
    "setup_guide": "Setup Guide (Developer Setup)",
    "developer_documentation": "Developer Guide",
    "user_documentation": "User Guide",
    "test_documentation": "Test Plan",
    "business_model": "Business Model",
    "marketing_plan": "Marketing Plan (GTM Strategy)",
    "support_playbook": "Support Playbook",
    "legal_compliance": "Legal & Compliance",
    "quality_reviewer": "Quality Review",
    "format_converter": "Format Conversions",
    "claude_cli_documentation": "Claude CLI Documentation",
}


def get_document_level(doc_type: str) -> DocumentLevel:
    """
    Get the level for a document type
    
    Args:
        doc_type: Document type identifier
    
    Returns:
        DocumentLevel enum value
    """
    # Normalize doc_type (remove underscores, lowercase)
    normalized = doc_type.lower().replace('_', '').replace('-', '')
    
    # Try direct match first
    if doc_type in DOCUMENT_LEVEL_MAPPING:
        return DOCUMENT_LEVEL_MAPPING[doc_type]
    
    # Try normalized match
    for key, level in DOCUMENT_LEVEL_MAPPING.items():
        key_normalized = key.lower().replace('_', '').replace('-', '')
        if key_normalized == normalized:
            return level
    
    # Default to cross-level if not found
    return DocumentLevel.CROSS_LEVEL


def get_document_display_name(doc_type: str) -> str:
    """
    Get human-readable display name for a document type
    
    Args:
        doc_type: Document type identifier
    
    Returns:
        Display name string
    """
    return DOCUMENT_DISPLAY_NAMES.get(doc_type, doc_type.replace('_', ' ').title())


def organize_documents_by_level(files: Dict[str, str]) -> Dict[DocumentLevel, List[Tuple[str, str]]]:
    """
    Organize documents by level
    
    Args:
        files: Dictionary mapping document types to file paths
    
    Returns:
        Dictionary mapping DocumentLevel to list of (doc_type, file_path) tuples
    """
    organized = {
        DocumentLevel.LEVEL_1_STRATEGIC: [],
        DocumentLevel.LEVEL_2_PRODUCT: [],
        DocumentLevel.LEVEL_3_TECHNICAL: [],
        DocumentLevel.CROSS_LEVEL: [],
    }
    
    for doc_type, file_path in files.items():
        level = get_document_level(doc_type)
        organized[level].append((doc_type, file_path))
    
    return organized


def format_documents_by_level(files: Dict[str, str], use_emoji: bool = True) -> str:
    """
    Format documents grouped by level for display
    
    Args:
        files: Dictionary mapping document types to file paths
        use_emoji: Whether to use emoji in output
    
    Returns:
        Formatted string with documents grouped by level
    """
    organized = organize_documents_by_level(files)
    
    output_lines = []
    
    # Level 1: Strategic
    if organized[DocumentLevel.LEVEL_1_STRATEGIC]:
        level_name = "🎯 Level 1: Strategic (Entrepreneur)" if use_emoji else "Level 1: Strategic (Entrepreneur)"
        output_lines.append(f"\n{level_name}")
        output_lines.append("=" * 60)
        for doc_type, file_path in organized[DocumentLevel.LEVEL_1_STRATEGIC]:
            display_name = get_document_display_name(doc_type)
            output_lines.append(f"  📄 {display_name}")
            output_lines.append(f"     → {file_path}")
    
    # Level 2: Product
    if organized[DocumentLevel.LEVEL_2_PRODUCT]:
        level_name = "📊 Level 2: Product (Product Manager)" if use_emoji else "Level 2: Product (Product Manager)"
        output_lines.append(f"\n{level_name}")
        output_lines.append("=" * 60)
        for doc_type, file_path in organized[DocumentLevel.LEVEL_2_PRODUCT]:
            display_name = get_document_display_name(doc_type)
            output_lines.append(f"  📄 {display_name}")
            output_lines.append(f"     → {file_path}")
    
    # Level 3: Technical
    if organized[DocumentLevel.LEVEL_3_TECHNICAL]:
        level_name = "💻 Level 3: Technical (Programmer)" if use_emoji else "Level 3: Technical (Programmer)"
        output_lines.append(f"\n{level_name}")
        output_lines.append("=" * 60)
        for doc_type, file_path in organized[DocumentLevel.LEVEL_3_TECHNICAL]:
            display_name = get_document_display_name(doc_type)
            output_lines.append(f"  📄 {display_name}")
            output_lines.append(f"     → {file_path}")
    
    # Cross-Level
    if organized[DocumentLevel.CROSS_LEVEL]:
        level_name = "🌐 Cross-Level (Everyone)" if use_emoji else "Cross-Level (Everyone)"
        output_lines.append(f"\n{level_name}")
        output_lines.append("=" * 60)
        for doc_type, file_path in organized[DocumentLevel.CROSS_LEVEL]:
            display_name = get_document_display_name(doc_type)
            output_lines.append(f"  📄 {display_name}")
            output_lines.append(f"     → {file_path}")
    
    return "\n".join(output_lines)


def get_documents_summary(files: Dict[str, str]) -> Dict[str, Dict]:
    """
    Get summary of documents organized by level (for API/JSON responses)
    
    Args:
        files: Dictionary mapping document types to file paths
    
    Returns:
        Dictionary with level-based organization
    """
    organized = organize_documents_by_level(files)
    
    summary = {
        "level_1_strategic": {
            "level_name": "Level 1: Strategic (Entrepreneur)",
            "documents": []
        },
        "level_2_product": {
            "level_name": "Level 2: Product (Product Manager)",
            "documents": []
        },
        "level_3_technical": {
            "level_name": "Level 3: Technical (Programmer)",
            "documents": []
        },
        "cross_level": {
            "level_name": "Cross-Level (Everyone)",
            "documents": []
        }
    }
    
    for doc_type, file_path in organized[DocumentLevel.LEVEL_1_STRATEGIC]:
        summary["level_1_strategic"]["documents"].append({
            "type": doc_type,
            "display_name": get_document_display_name(doc_type),
            "file_path": file_path
        })
    
    for doc_type, file_path in organized[DocumentLevel.LEVEL_2_PRODUCT]:
        summary["level_2_product"]["documents"].append({
            "type": doc_type,
            "display_name": get_document_display_name(doc_type),
            "file_path": file_path
        })
    
    for doc_type, file_path in organized[DocumentLevel.LEVEL_3_TECHNICAL]:
        summary["level_3_technical"]["documents"].append({
            "type": doc_type,
            "display_name": get_document_display_name(doc_type),
            "file_path": file_path
        })
    
    for doc_type, file_path in organized[DocumentLevel.CROSS_LEVEL]:
        summary["cross_level"]["documents"].append({
            "type": doc_type,
            "display_name": get_document_display_name(doc_type),
            "file_path": file_path
        })
    
    return summary


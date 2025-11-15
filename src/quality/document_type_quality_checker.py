"""
Document Type-Aware Quality Checker
Provides document-type-specific quality checking with appropriate thresholds
Uses quality_rules.json for configuration
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from src.quality.quality_checker import QualityChecker
from src.context.shared_context import AgentType
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Load quality rules from JSON file
def _load_quality_rules() -> Dict[str, Dict]:
    """Load quality rules from quality_rules.json"""
    try:
        # Try to find the file in config directory
        config_path = Path(__file__).parent.parent / "config" / "quality_rules.json"
        if not config_path.exists():
            # Fallback to current directory
            config_path = Path("src/config/quality_rules.json")
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                logger.info(f"Loaded quality rules from {config_path}")
                return rules
        else:
            logger.warning(f"Quality rules file not found at {config_path}, using defaults")
            return {}
    except Exception as e:
        logger.error(f"Error loading quality rules: {e}", exc_info=True)
        return {}

# Load rules at module level
QUALITY_RULES = _load_quality_rules()

# Legacy document type-specific quality requirements (fallback)
DOCUMENT_TYPE_REQUIREMENTS = {
    AgentType.REQUIREMENTS_ANALYST: {
        "min_words": 300,
        "required_sections": [
            r"^#+\s+Project\s+Overview",
            r"^#+\s+Core\s+Features",
            r"^#+\s+Technical\s+Requirements",
            r"^#+\s+User\s+Personas",
            r"^#+\s+Business\s+Objectives",
            r"^#+\s+Constraints"
        ],
        "min_readability": 50.0
    },
    AgentType.PROJECT_CHARTER: {
        "min_words": 500,
        "required_sections": [
            r"^#+\s+(Executive\s+)?Summary",
            r"^#+\s+Project\s+Overview",
            r"^#+\s+(Business\s+)?Objectives",
            r"^#+\s+Scope",
            r"^#+\s+Stakeholders"
        ],
        "min_readability": 50.0
    },
    AgentType.PM_DOCUMENTATION: {
        "min_words": 800,
        "required_sections": [
            r"^#+\s+Project\s+Timeline",
            r"^#+\s+Resource\s+Requirements",
            r"^#+\s+Budget",
            r"^#+\s+Risk",
            r"^#+\s+Success\s+Metrics"
        ],
        "min_readability": 50.0
    },
    AgentType.USER_STORIES: {
        "min_words": 400,
        "required_sections": [
            r"^#+\s+User\s+Stories",
            r"^#+\s+(Acceptance\s+)?Criteria",
            r"^#+\s+Epic",
            r"^#+\s+(Feature|Feature\s+Breakdown)"
        ],
        "min_readability": 50.0
    },
    AgentType.TECHNICAL_DOCUMENTATION: {
        "min_words": 1000,
        "required_sections": [
            r"^#+\s+System\s+Architecture",
            r"^#+\s+Technical\s+Stack",
            r"^#+\s+Database\s+Design",
            r"^#+\s+API\s+Design",
            r"^#+\s+Security"
        ],
        "min_readability": 45.0
    },
    AgentType.DATABASE_SCHEMA: {
        "min_words": 600,
        "required_sections": [
            r"^#+\s+Database\s+Overview",
            r"^#+\s+(Schema|Table)",
            r"^#+\s+(Relationship|Entity)",
            r"^#+\s+(Index|Indexing)"
        ],
        "min_readability": 45.0
    },
    AgentType.API_DOCUMENTATION: {
        "min_words": 800,
        "required_sections": [
            r"^#+\s+API\s+Overview",
            r"^#+\s+Authentication",
            r"^#+\s+Endpoint",
            r"^#+\s+(Data\s+)?Model",
            r"^#+\s+Error"
        ],
        "min_readability": 50.0
    },
    AgentType.SETUP_GUIDE: {
        "min_words": 600,
        "required_sections": [
            r"^#+\s+Prerequisite",
            r"^#+\s+Installation",
            r"^#+\s+(Setup|Configuration)",
            r"^#+\s+(Running|Start)",
            r"^#+\s+Troubleshooting"
        ],
        "min_readability": 60.0
    },
    AgentType.DEVELOPER_DOCUMENTATION: {
        "min_words": 800,
        "required_sections": [
            r"^#+\s+(Getting\s+)?Started",
            r"^#+\s+(Architecture|Structure)",
            r"^#+\s+(Development|Coding)",
            r"^#+\s+(Testing|Test)",
            r"^#+\s+(Deployment|Deploy)"
        ],
        "min_readability": 50.0
    },
    AgentType.STAKEHOLDER_COMMUNICATION: {
        "min_words": 400,
        "required_sections": [
            r"^#+\s+(Executive\s+)?Summary",
            r"^#+\s+(Key\s+)?(Point|Highlight)",
            r"^#+\s+(Impact|Benefit)",
            r"^#+\s+(Next\s+)?Step"
        ],
        "min_readability": 60.0
    },
    AgentType.TEST_DOCUMENTATION: {
        "min_words": 600,
        "required_sections": [
            r"^#+\s+Test\s+(Strategy|Plan)",
            r"^#+\s+Test\s+Case",
            r"^#+\s+Test\s+Scenario",
            r"^#+\s+(Test\s+)?Environment",
            r"^#+\s+(Test\s+)?(Coverage|Result)"
        ],
        "min_readability": 50.0
    },
    AgentType.USER_DOCUMENTATION: {
        "min_words": 500,
        "required_sections": [
            r"^#+\s+Introduction",
            r"^#+\s+(Installation|Setup)",
            r"^#+\s+(Usage|Basic|Getting\s+Started)",
            r"^#+\s+Feature",
            r"^#+\s+(Troubleshooting|FAQ)"
        ],
        "min_readability": 65.0
    },
    AgentType.BUSINESS_MODEL: {
        "min_words": 600,
        "required_sections": [
            r"^#+\s+(Executive\s+)?Summary",
            r"^#+\s+Business\s+Model",
            r"^#+\s+(Revenue|Monetization)",
            r"^#+\s+(Market|Target)",
            r"^#+\s+(Competitive|Competition)"
        ],
        "min_readability": 55.0
    },
    AgentType.MARKETING_PLAN: {
        "min_words": 700,
        "required_sections": [
            r"^#+\s+(Executive\s+)?Summary",
            r"^#+\s+(Marketing\s+)?Strategy",
            r"^#+\s+(Channel|Campaign)",
            r"^#+\s+(Budget|Cost)",
            r"^#+\s+(Metric|KPI|Performance)"
        ],
        "min_readability": 55.0
    },
    AgentType.SUPPORT_PLAYBOOK: {
        "min_words": 500,
        "required_sections": [
            r"^#+\s+(Support|Troubleshooting)",
            r"^#+\s+(Common|Issue)",
            r"^#+\s+(Escalation|Process)",
            r"^#+\s+(Resolution|Solution)",
            r"^#+\s+(FAQ|Help)"
        ],
        "min_readability": 60.0
    },
    AgentType.LEGAL_COMPLIANCE: {
        "min_words": 500,
        "required_sections": [
            r"^#+\s+(Privacy|Legal)",
            r"^#+\s+(Compliance|Regulation)",
            r"^#+\s+(Data\s+)?(Handling|Protection)",
            r"^#+\s+(License|License\s+Compatibility)",
            r"^#+\s+(Policy|Term)"
        ],
        "min_readability": 45.0
    }
}


class DocumentTypeQualityChecker:
    """Quality checker with document-type-specific requirements"""
    
    def __init__(self):
        """Initialize document type quality checker"""
        self.base_checker = QualityChecker()
    
    def _convert_section_to_regex(self, section_name: str) -> str:
        """Convert section name to regex pattern for matching markdown headings"""
        # Escape special regex characters, but allow / and spaces
        escaped = re.escape(section_name)
        # Replace escaped spaces with \s+ to allow flexible spacing
        escaped = escaped.replace(r'\ ', r'\s+')
        # Replace / with optional space
        escaped = escaped.replace(r'\/', r'[/\s]+')
        # Match any heading level (#, ##, ###, etc.)
        return rf"^#+\s+{escaped}"
    
    def _parse_readability_target(self, target_str: str) -> float:
        """Parse readability target range (e.g., '50-65') and return minimum value"""
        try:
            if '-' in target_str:
                min_val, max_val = target_str.split('-')
                return float(min_val.strip())
            else:
                return float(target_str.strip())
        except (ValueError, AttributeError):
            return 50.0  # Default
    
    def get_requirements_for_type(self, document_type: str) -> Dict:
        """
        Get quality requirements for a specific document type
        First tries quality_rules.json, then falls back to legacy DOCUMENT_TYPE_REQUIREMENTS
        
        Args:
            document_type: Document type (document name or AgentType enum value)
            
        Returns:
            Dict with min_words, required_sections, min_readability, and optional fields
        """
        # Normalize document type for matching
        doc_type_normalized = document_type.strip()
        doc_type_lower = doc_type_normalized.lower().replace('_', ' ').replace('-', ' ')
        
        # First, try to find in quality_rules.json
        if QUALITY_RULES:
            # Try exact match
            if doc_type_normalized in QUALITY_RULES:
                rules = QUALITY_RULES[doc_type_normalized]
                # Convert to format expected by QualityChecker
                required_sections = [
                    self._convert_section_to_regex(section)
                    for section in rules.get("required_sections", [])
                ]
                
                return {
                    "min_words": rules.get("min_word_count", 500),
                    "required_sections": required_sections,
                    "min_readability": self._parse_readability_target(
                        rules.get("readability_target", "50-70")
                    ),
                    "readability_target": rules.get("readability_target", "50-70"),
                    "optional_sections": rules.get("optional_sections", []),
                    "llm_focus": rules.get("llm_focus", []),
                    "auto_fail": rules.get("auto_fail", []),
                    "source": "quality_rules.json"
                }
            
            # Try fuzzy match (case-insensitive, partial)
            for rule_name, rules in QUALITY_RULES.items():
                rule_name_lower = rule_name.lower()
                if (doc_type_lower in rule_name_lower or 
                    rule_name_lower in doc_type_lower or
                    doc_type_normalized.lower() == rule_name_lower):
                    # Convert to format expected by QualityChecker
                    required_sections = [
                        self._convert_section_to_regex(section)
                        for section in rules.get("required_sections", [])
                    ]
                    
                    return {
                        "min_words": rules.get("min_word_count", 500),
                        "required_sections": required_sections,
                        "min_readability": self._parse_readability_target(
                            rules.get("readability_target", "50-70")
                        ),
                        "readability_target": rules.get("readability_target", "50-70"),
                        "optional_sections": rules.get("optional_sections", []),
                        "llm_focus": rules.get("llm_focus", []),
                        "auto_fail": rules.get("auto_fail", []),
                        "source": "quality_rules.json"
                    }
        
        # Fallback to legacy DOCUMENT_TYPE_REQUIREMENTS
        # Try exact match first
        for agent_type, requirements in DOCUMENT_TYPE_REQUIREMENTS.items():
            if agent_type.value.lower() == document_type.lower():
                return {**requirements, "source": "legacy"}
        
        # Try partial match
        for agent_type, requirements in DOCUMENT_TYPE_REQUIREMENTS.items():
            if doc_type_lower in agent_type.value.lower() or agent_type.value.lower() in doc_type_lower:
                return {**requirements, "source": "legacy"}
        
        # Default requirements for unknown types
        return {
            "min_words": 500,
            "required_sections": [
                r"^#+\s+.*",  # At least one section
            ],
            "min_readability": 50.0,
            "readability_target": "50-70",
            "optional_sections": [],
            "llm_focus": [],
            "auto_fail": [],
            "source": "default"
        }
    
    def _check_auto_fail(self, content: str, auto_fail_rules: List[str]) -> Dict:
        """
        Check if document fails any auto_fail rules
        
        Args:
            content: Document content
            auto_fail_rules: List of auto-fail conditions (e.g., ["Missing Scope OR Goals", "No milestones"])
            
        Returns:
            Dict with auto_fail_passed, auto_fail_violations
        """
        violations = []
        
        for rule in auto_fail_rules:
            rule_lower = rule.lower()
            
            # Handle OR conditions (e.g., "Missing Scope OR Goals")
            if " or " in rule_lower:
                parts = [p.strip() for p in rule.split(" OR ", 1)]
                # Check if NEITHER part is found
                found_any = False
                for part in parts:
                    # Remove "Missing" prefix if present
                    part_clean = part.replace("missing", "").strip()
                    if part_clean:
                        # Check if section exists
                        pattern = self._convert_section_to_regex(part_clean)
                        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                            found_any = True
                            break
                
                if not found_any:
                    violations.append(rule)
            
            # Handle "No X" or "Missing X" patterns
            elif rule_lower.startswith("no ") or rule_lower.startswith("missing "):
                # Extract the key term
                if rule_lower.startswith("no "):
                    key_term = rule_lower[3:].strip()
                else:  # "missing "
                    key_term = rule_lower[8:].strip()
                
                # Check if term/section exists
                pattern = self._convert_section_to_regex(key_term)
                if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    # Also check if key term appears in content (case-insensitive)
                    if key_term.lower() not in content.lower():
                        violations.append(rule)
            
            # Handle other patterns (e.g., "Completely missing dependencies")
            else:
                # Extract key terms and check
                key_terms = re.findall(r'\b\w+\b', rule_lower)
                # Skip common words
                skip_words = {"missing", "no", "completely", "unclear", "not", "the", "a", "an"}
                key_terms = [t for t in key_terms if t not in skip_words]
                
                if key_terms:
                    # Check if any key term appears
                    found = False
                    for term in key_terms:
                        if term in content.lower():
                            found = True
                            break
                    if not found:
                        violations.append(rule)
        
        return {
            "auto_fail_passed": len(violations) == 0,
            "auto_fail_violations": violations
        }
    
    def check_quality_for_type(
        self,
        content: str,
        document_type: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Check quality for a specific document type
        
        Args:
            content: Document content
            document_type: Document type (AgentType enum value or string)
            weights: Custom weights for overall score calculation
            
        Returns:
            Comprehensive quality report with auto_fail checks
        """
        # Get requirements for this document type
        requirements = self.get_requirements_for_type(document_type)
        
        # Create checker with document-type-specific requirements
        checker = QualityChecker(
            min_words=requirements["min_words"],
            required_sections=requirements["required_sections"],
            min_readability_score=requirements["min_readability"]
        )
        
        # Run quality check
        result = checker.check_quality(content, weights=weights)
        
        # Check auto_fail rules
        auto_fail_rules = requirements.get("auto_fail", [])
        if auto_fail_rules:
            auto_fail_result = self._check_auto_fail(content, auto_fail_rules)
            result["auto_fail"] = auto_fail_result
            
            # If auto_fail, mark overall as failed regardless of score
            if not auto_fail_result["auto_fail_passed"]:
                result["passed"] = False
                result["overall_score"] = min(result.get("overall_score", 100), 40)  # Cap at 40 if auto-fail
                logger.warning(
                    f"Document {document_type} auto-failed due to: {auto_fail_result['auto_fail_violations']}"
                )
        
        # Add document type info and additional metadata to result
        result["document_type"] = document_type
        result["requirements"] = requirements
        result["llm_focus"] = requirements.get("llm_focus", [])
        result["optional_sections"] = requirements.get("optional_sections", [])
        result["readability_target"] = requirements.get("readability_target", "50-70")
        
        return result
    
    def get_all_checklists(self) -> Dict[AgentType, List[str]]:
        """
        Get all quality checklists mapped by AgentType
        
        Returns:
            Dict mapping AgentType to list of required section patterns
        """
        return {
            agent_type: requirements["required_sections"]
            for agent_type, requirements in DOCUMENT_TYPE_REQUIREMENTS.items()
        }
    
    def get_checklist_for_agent(self, agent_type: AgentType) -> Optional[List[str]]:
        """
        Get quality checklist for a specific agent type
        
        Args:
            agent_type: AgentType enum value
            
        Returns:
            List of required section patterns, or None if not found
        """
        requirements = DOCUMENT_TYPE_REQUIREMENTS.get(agent_type)
        if requirements:
            return requirements["required_sections"]
        return None
    
    def check_multiple_documents(
        self,
        documents: Dict[str, str],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict]:
        """
        Check quality for multiple documents
        
        Args:
            documents: Dict mapping document names/types to content
            weights: Custom weights for overall score calculation
            
        Returns:
            Dict mapping document names to quality reports
        """
        results = {}
        
        for doc_name, doc_content in documents.items():
            try:
                # Extract document type from name
                doc_type = self._extract_document_type(doc_name)
                
                # Check quality
                result = self.check_quality_for_type(
                    doc_content,
                    doc_type,
                    weights=weights
                )
                
                results[doc_name] = result
            except Exception as e:
                # If check fails, provide minimal result
                results[doc_name] = {
                    "overall_score": 0,
                    "passed": False,
                    "error": str(e),
                    "document_type": doc_name
                }
        
        return results
    
    def _extract_document_type(self, doc_name: str) -> str:
        """
        Extract document type from document name
        
        Args:
            doc_name: Document name (e.g., "requirements.md", "technical_documentation")
            
        Returns:
            Document type string
        """
        # Remove file extension
        doc_name = doc_name.replace('.md', '').replace('.txt', '')
        
        # Map common names to agent types
        name_mapping = {
            "requirements": AgentType.REQUIREMENTS_ANALYST.value,
            "project_charter": AgentType.PROJECT_CHARTER.value,
            "charter": AgentType.PROJECT_CHARTER.value,
            "pm_documentation": AgentType.PM_DOCUMENTATION.value,
            "project_plan": AgentType.PM_DOCUMENTATION.value,
            "pm": AgentType.PM_DOCUMENTATION.value,
            "user_stories": AgentType.USER_STORIES.value,
            "technical_documentation": AgentType.TECHNICAL_DOCUMENTATION.value,
            "technical_spec": AgentType.TECHNICAL_DOCUMENTATION.value,
            "technical": AgentType.TECHNICAL_DOCUMENTATION.value,
            "database_schema": AgentType.DATABASE_SCHEMA.value,
            "database": AgentType.DATABASE_SCHEMA.value,
            "api_documentation": AgentType.API_DOCUMENTATION.value,
            "api": AgentType.API_DOCUMENTATION.value,
            "setup_guide": AgentType.SETUP_GUIDE.value,
            "setup": AgentType.SETUP_GUIDE.value,
            "developer_documentation": AgentType.DEVELOPER_DOCUMENTATION.value,
            "developer_guide": AgentType.DEVELOPER_DOCUMENTATION.value,
            "developer": AgentType.DEVELOPER_DOCUMENTATION.value,
            "stakeholder_communication": AgentType.STAKEHOLDER_COMMUNICATION.value,
            "stakeholder": AgentType.STAKEHOLDER_COMMUNICATION.value,
            "test_documentation": AgentType.TEST_DOCUMENTATION.value,
            "test": AgentType.TEST_DOCUMENTATION.value,
            "user_documentation": AgentType.USER_DOCUMENTATION.value,
            "user_guide": AgentType.USER_DOCUMENTATION.value,
            "user": AgentType.USER_DOCUMENTATION.value,
            "business_model": AgentType.BUSINESS_MODEL.value,
            "business": AgentType.BUSINESS_MODEL.value,
            "marketing_plan": AgentType.MARKETING_PLAN.value,
            "marketing": AgentType.MARKETING_PLAN.value,
            "support_playbook": AgentType.SUPPORT_PLAYBOOK.value,
            "support": AgentType.SUPPORT_PLAYBOOK.value,
            "legal_compliance": AgentType.LEGAL_COMPLIANCE.value,
            "legal": AgentType.LEGAL_COMPLIANCE.value,
        }
        
        # Try to find matching type
        doc_name_lower = doc_name.lower()
        for key, agent_type in name_mapping.items():
            if key in doc_name_lower:
                return agent_type
        
        # Return as-is if no match
        return doc_name


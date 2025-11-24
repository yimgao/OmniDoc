"""
Shared Context Data Structures
Defines data models for agent collaboration
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Types of documentation agents"""
    # Level 1: Strategic (Entrepreneur)
    REQUIREMENTS_ANALYST = "requirements_analyst"
    STAKEHOLDER_COMMUNICATION = "stakeholder_communication"
    PROJECT_CHARTER = "project_charter"
    
    # Level 2: Product (Product Manager)
    PM_DOCUMENTATION = "pm_documentation"
    USER_STORIES = "user_stories"
    WBS_AGENT = "wbs_agent"  # Work Breakdown Structure
    
    # Level 3: Technical (Programmer)
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    API_DOCUMENTATION = "api_documentation"
    DATABASE_SCHEMA = "database_schema"
    SETUP_GUIDE = "setup_guide"
    
    # Business & Marketing (Level 1-2)
    MARKETING_PLAN = "marketing_plan"
    BUSINESS_MODEL = "business_model"
    SUPPORT_PLAYBOOK = "support_playbook"
    LEGAL_COMPLIANCE = "legal_compliance"
    
    # Cross-Level
    DEVELOPER_DOCUMENTATION = "developer_documentation"
    USER_DOCUMENTATION = "user_documentation"
    TEST_DOCUMENTATION = "test_documentation"
    QUALITY_REVIEWER = "quality_reviewer"
    FORMAT_CONVERTER = "format_converter"
    CLAUDE_CLI_DOCUMENTATION = "claude_cli_documentation"


class DocumentStatus(str, Enum):
    """Status of document generation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RequirementsDocument:
    """Requirements document structure"""
    user_idea: str
    project_overview: str
    core_features: List[str]
    technical_requirements: Dict
    user_personas: List[Dict]
    business_objectives: List[str]
    constraints: List[str]
    assumptions: List[str]
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentOutput:
    """Output from a documentation agent"""
    agent_type: AgentType
    document_type: str  # e.g., "project_plan", "technical_spec"
    content: str  # Markdown content (stored in database)
    file_path: Optional[str] = None  # Optional virtual path for reference (not used for file storage)
    quality_score: Optional[float] = None
    status: DocumentStatus = DocumentStatus.PENDING
    generated_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)  # IDs of dependent documents


@dataclass
class CrossReference:
    """Cross-reference between documents"""
    from_document: str  # Document ID
    to_document: str  # Document ID
    reference_type: str  # "requires", "implements", "references"
    description: Optional[str] = None


@dataclass
class SharedContext:
    """Main shared context structure"""
    project_id: str
    user_idea: str
    
    # Requirements
    requirements: Optional[RequirementsDocument] = None
    
    # Agent outputs
    agent_outputs: Dict[AgentType, AgentOutput] = field(default_factory=dict)
    
    # Cross-references
    cross_references: List[CrossReference] = field(default_factory=list)
    
    # Workflow state
    workflow_status: Dict[AgentType, DocumentStatus] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_requirements_summary(self) -> Dict:
        """Get a summary of requirements for other agents"""
        if not self.requirements:
            return {}
        
        return {
            "user_idea": self.requirements.user_idea,
            "project_overview": self.requirements.project_overview,
            "core_features": self.requirements.core_features,
            "technical_requirements": self.requirements.technical_requirements,
            "user_personas": self.requirements.user_personas,
            "business_objectives": self.requirements.business_objectives,
            "constraints": self.requirements.constraints,
            "assumptions": self.requirements.assumptions,
        }
    
    def get_agent_output(self, agent_type: AgentType) -> Optional[AgentOutput]:
        """Get output from a specific agent"""
        return self.agent_outputs.get(agent_type)
    
    def add_agent_output(self, output: AgentOutput):
        """Add or update agent output"""
        self.agent_outputs[output.agent_type] = output
        self.workflow_status[output.agent_type] = output.status
        self.updated_at = datetime.now()
    
    def is_agent_complete(self, agent_type: AgentType) -> bool:
        """Check if an agent has completed its task"""
        status = self.workflow_status.get(agent_type, DocumentStatus.PENDING)
        return status == DocumentStatus.COMPLETE
    
    def get_available_dependencies(self) -> Dict[str, AgentOutput]:
        """Get all completed agent outputs as dependencies"""
        return {
            agent_type.value: output
            for agent_type, output in self.agent_outputs.items()
            if output.status == DocumentStatus.COMPLETE
        }


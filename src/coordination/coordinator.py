"""
Workflow Coordinator
Orchestrates multi-agent documentation generation workflow
"""
from typing import Optional, Dict, List
from datetime import datetime
import uuid

from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, SharedContext
from src.agents.requirements_analyst import RequirementsAnalyst
from src.agents.pm_documentation_agent import PMDocumentationAgent
from src.agents.technical_documentation_agent import TechnicalDocumentationAgent
from src.agents.api_documentation_agent import APIDocumentationAgent
from src.agents.developer_documentation_agent import DeveloperDocumentationAgent
from src.rate_limit.queue_manager import RequestQueue


class WorkflowCoordinator:
    """
    Coordinates the multi-agent documentation generation workflow
    
    Workflow:
    1. Requirements Analyst → Requirements Doc
    2. PM Agent → Project Management Docs
    3. (Future: Technical, API, Developer, Stakeholder agents)
    """
    
    def __init__(
        self,
        context_manager: Optional[ContextManager] = None,
        rate_limiter: Optional[RequestQueue] = None
    ):
        """
        Initialize workflow coordinator
        
        Args:
            context_manager: Context manager instance
            rate_limiter: Shared rate limiter for all agents
        """
        self.context_manager = context_manager or ContextManager()
        self.rate_limiter = rate_limiter or RequestQueue(max_rate=60, period=60)
        
        # Initialize agents (shared rate limiter)
        self.requirements_analyst = RequirementsAnalyst(rate_limiter=self.rate_limiter)
        self.pm_agent = PMDocumentationAgent(rate_limiter=self.rate_limiter)
        self.technical_agent = TechnicalDocumentationAgent(rate_limiter=self.rate_limiter)
        self.api_agent = APIDocumentationAgent(rate_limiter=self.rate_limiter)
        self.developer_agent = DeveloperDocumentationAgent(rate_limiter=self.rate_limiter)
    
    def generate_all_docs(self, user_idea: str, project_id: Optional[str] = None) -> Dict:
        """
        Generate all documentation types from a user idea
        
        Args:
            user_idea: User's project idea
            project_id: Optional project ID (generates one if not provided)
        
        Returns:
            Dict with generated file paths and status
        """
        # Generate project ID if not provided
        if not project_id:
            project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        print("=" * 60)
        print(f"🚀 Starting Multi-Agent Documentation Generation")
        print(f"📋 Project ID: {project_id}")
        print(f"💡 User Idea: {user_idea}")
        print("=" * 60)
        print()
        
        results = {
            "project_id": project_id,
            "user_idea": user_idea,
            "files": {},
            "status": {}
        }
        
        try:
            # Step 1: Requirements Analyst
            print("📝 Step 1: Generating Requirements...")
            print("-" * 60)
            req_path = self.requirements_analyst.generate_and_save(
                user_idea=user_idea,
                output_filename="requirements.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["requirements"] = req_path
            results["status"]["requirements"] = "complete"
            print()
            
            # Step 2: Get requirements from context
            print("📖 Step 2: Retrieving requirements for PM agent...")
            print("-" * 60)
            context = self.context_manager.get_shared_context(project_id)
            if not context.requirements:
                raise ValueError("Requirements not found in context")
            
            # Build requirements summary
            req_summary = {
                "user_idea": context.requirements.user_idea,
                "project_overview": context.requirements.project_overview,
                "core_features": context.requirements.core_features,
                "technical_requirements": context.requirements.technical_requirements
            }
            print("✅ Requirements retrieved from context")
            print()
            
            # Step 3: PM Documentation Agent
            print("📊 Step 3: Generating Project Management Documentation...")
            print("-" * 60)
            pm_path = self.pm_agent.generate_and_save(
                requirements_summary=req_summary,
                output_filename="project_plan.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["pm_documentation"] = pm_path
            results["status"]["pm_documentation"] = "complete"
            print()
            
            # Step 4: Technical Documentation Agent
            print("🔧 Step 4: Generating Technical Documentation...")
            print("-" * 60)
            technical_path = self.technical_agent.generate_and_save(
                requirements_summary=req_summary,
                output_filename="technical_spec.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["technical_documentation"] = technical_path
            results["status"]["technical_documentation"] = "complete"
            print()
            
            # Step 5: Get technical documentation for API agent
            print("📖 Step 5: Retrieving technical documentation for API agent...")
            print("-" * 60)
            technical_output = self.context_manager.get_agent_output(project_id, AgentType.TECHNICAL_DOCUMENTATION)
            technical_summary = technical_output.content if technical_output else None
            print("✅ Technical documentation retrieved")
            print()
            
            # Step 6: API Documentation Agent
            print("🔌 Step 6: Generating API Documentation...")
            print("-" * 60)
            api_path = self.api_agent.generate_and_save(
                requirements_summary=req_summary,
                technical_summary=technical_summary,
                output_filename="api_documentation.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["api_documentation"] = api_path
            results["status"]["api_documentation"] = "complete"
            print()
            
            # Step 7: Get API documentation for developer agent
            print("📖 Step 7: Retrieving API documentation for developer agent...")
            print("-" * 60)
            api_output = self.context_manager.get_agent_output(project_id, AgentType.API_DOCUMENTATION)
            api_summary = api_output.content if api_output else None
            print("✅ API documentation retrieved")
            print()
            
            # Step 8: Developer Documentation Agent
            print("👨‍💻 Step 8: Generating Developer Documentation...")
            print("-" * 60)
            developer_path = self.developer_agent.generate_and_save(
                requirements_summary=req_summary,
                technical_summary=technical_summary,
                api_summary=api_summary,
                output_filename="developer_guide.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["developer_documentation"] = developer_path
            results["status"]["developer_documentation"] = "complete"
            print()
            
            # Summary
            print("=" * 60)
            print("✅ Multi-Agent Workflow Complete!")
            print("=" * 60)
            print(f"📄 Generated Files:")
            for doc_type, file_path in results["files"].items():
                print(f"   - {doc_type}: {file_path}")
            print()
            print(f"📊 Status: {len(results['files'])} documents generated")
            print(f"💾 Context: Saved to project {project_id}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error in workflow: {e}")
            import traceback
            traceback.print_exc()
            results["error"] = str(e)
            return results
    
    def get_workflow_status(self, project_id: str) -> Dict:
        """Get current workflow status for a project"""
        context = self.context_manager.get_shared_context(project_id)
        
        return {
            "project_id": project_id,
            "workflow_status": {
                agent_type.value: status.value
                for agent_type, status in context.workflow_status.items()
            },
            "completed_agents": [
                agent_type.value
                for agent_type, status in context.workflow_status.items()
                if status == DocumentStatus.COMPLETE
            ],
            "total_outputs": len(context.agent_outputs)
        }


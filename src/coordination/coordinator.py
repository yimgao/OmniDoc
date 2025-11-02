"""
Workflow Coordinator
Orchestrates multi-agent documentation generation workflow
"""
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
import uuid

from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, SharedContext
from src.agents.requirements_analyst import RequirementsAnalyst
from src.agents.pm_documentation_agent import PMDocumentationAgent
from src.agents.technical_documentation_agent import TechnicalDocumentationAgent
from src.agents.api_documentation_agent import APIDocumentationAgent
from src.agents.developer_documentation_agent import DeveloperDocumentationAgent
from src.agents.stakeholder_communication_agent import StakeholderCommunicationAgent
from src.agents.user_documentation_agent import UserDocumentationAgent
from src.agents.test_documentation_agent import TestDocumentationAgent
from src.agents.quality_reviewer_agent import QualityReviewerAgent
from src.agents.format_converter_agent import FormatConverterAgent
from src.utils.file_manager import FileManager
from src.utils.cross_referencer import CrossReferencer
from src.utils.parallel_executor import ParallelExecutor, TaskStatus
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
        self.file_manager = FileManager(base_dir="docs")
        
        # Initialize agents (shared rate limiter)
        self.requirements_analyst = RequirementsAnalyst(rate_limiter=self.rate_limiter)
        self.pm_agent = PMDocumentationAgent(rate_limiter=self.rate_limiter)
        self.technical_agent = TechnicalDocumentationAgent(rate_limiter=self.rate_limiter)
        self.api_agent = APIDocumentationAgent(rate_limiter=self.rate_limiter)
        self.developer_agent = DeveloperDocumentationAgent(rate_limiter=self.rate_limiter)
        self.stakeholder_agent = StakeholderCommunicationAgent(rate_limiter=self.rate_limiter)
        self.user_agent = UserDocumentationAgent(rate_limiter=self.rate_limiter)
        self.test_agent = TestDocumentationAgent(rate_limiter=self.rate_limiter)
        self.quality_reviewer = QualityReviewerAgent(rate_limiter=self.rate_limiter)
        self.format_converter = FormatConverterAgent(rate_limiter=self.rate_limiter)
        self.cross_referencer = CrossReferencer()
    
    def _generate_technical_doc(self, req_summary, project_id):
        """Helper for parallel technical doc generation"""
        return self.technical_agent.generate_and_save(
            requirements_summary=req_summary,
            output_filename="technical_spec.md",
            project_id=project_id,
            context_manager=self.context_manager
        )
    
    def _generate_stakeholder_doc(self, req_summary, pm_path, project_id):
        """Helper for parallel stakeholder doc generation"""
        pm_summary = self._get_summary_from_file(pm_path)
        return self.stakeholder_agent.generate_and_save(
            requirements_summary=req_summary,
            pm_summary=pm_summary,
            output_filename="stakeholder_summary.md",
            project_id=project_id,
            context_manager=self.context_manager
        )
    
    def _generate_user_doc(self, req_summary, project_id):
        """Helper for parallel user doc generation"""
        return self.user_agent.generate_and_save(
            requirements_summary=req_summary,
            output_filename="user_guide.md",
            project_id=project_id,
            context_manager=self.context_manager
        )
    
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
            
            # Step 9: Get PM documentation for stakeholder agent
            print("📖 Step 9: Retrieving PM documentation for stakeholder agent...")
            print("-" * 60)
            pm_output = self.context_manager.get_agent_output(project_id, AgentType.PM_DOCUMENTATION)
            pm_summary = pm_output.content if pm_output else None
            print("✅ PM documentation retrieved")
            print()
            
            # Step 10: Stakeholder Communication Agent
            print("👔 Step 10: Generating Stakeholder Communication Document...")
            print("-" * 60)
            stakeholder_path = self.stakeholder_agent.generate_and_save(
                requirements_summary=req_summary,
                pm_summary=pm_summary,
                output_filename="stakeholder_summary.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["stakeholder_documentation"] = stakeholder_path
            results["status"]["stakeholder_documentation"] = "complete"
            print()
            
            
            # Step 12: Test Documentation Agent
            print("🧪 Step 12: Generating Test Documentation...")
            print("-" * 60)
            test_path = self.test_agent.generate_and_save(
                requirements_summary=req_summary,
                technical_summary=technical_summary,
                output_filename="test_plan.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["test_documentation"] = test_path
            results["status"]["test_documentation"] = "complete"
            print()
            
            # Step 13: Collect all documentation for cross-referencing and quality review
            print("📚 Step 13: Collecting all documentation...")
            print("-" * 60)
            all_documentation = {}
            document_agent_types = {}
            document_file_paths = {}
            
            # Map document types to agent types
            doc_type_to_agent = {
                "requirements": AgentType.REQUIREMENTS_ANALYST,
                "pm_documentation": AgentType.PM_DOCUMENTATION,
                "technical_documentation": AgentType.TECHNICAL_DOCUMENTATION,
                "api_documentation": AgentType.API_DOCUMENTATION,
                "developer_documentation": AgentType.DEVELOPER_DOCUMENTATION,
                "stakeholder_documentation": AgentType.STAKEHOLDER_COMMUNICATION,
                "user_documentation": AgentType.USER_DOCUMENTATION,
                "test_documentation": AgentType.TEST_DOCUMENTATION
            }
            
            for doc_type, file_path in results["files"].items():
                if file_path and doc_type != "quality_review" and doc_type != "format_conversions":
                    try:
                        from src.utils.file_manager import FileManager
                        file_manager = FileManager()
                        content = file_manager.read_file(file_path)
                        
                        # Map to agent type if available
                        agent_type = doc_type_to_agent.get(doc_type)
                        if agent_type:
                            all_documentation[agent_type] = content
                            document_agent_types[doc_type] = agent_type
                            document_file_paths[agent_type] = file_path
                    except Exception as e:
                        print(f"⚠️  Warning: Could not read {doc_type}: {e}")
            
            print(f"✅ Collected {len(all_documentation)} documents")
            print()
            
            # Step 13.5: Add cross-references to all documents
            print("🔗 Step 13.5: Adding cross-references between documents...")
            print("-" * 60)
            try:
                referenced_docs = self.cross_referencer.create_cross_references(
                    all_documentation,
                    document_file_paths
                )
                
                # Save cross-referenced documents back to files
                updated_count = 0
                for agent_type, referenced_content in referenced_docs.items():
                    original_content = all_documentation.get(agent_type)
                    if referenced_content != original_content:
                        file_path = document_file_paths[agent_type]
                        self.file_manager.write_file(Path(file_path).name, referenced_content)
                        # Update all_documentation for quality review
                        all_documentation[agent_type] = referenced_content
                        updated_count += 1
                
                print(f"✅ Added cross-references to {updated_count} documents")
                print()
                
                # Generate document index
                print("📑 Generating document index...")
                print("-" * 60)
                try:
                    index_content = self.cross_referencer.generate_document_index(
                        all_documentation,
                        document_file_paths,
                        project_name=req_summary.get('project_overview', 'Project')[:50]
                    )
                    
                    index_path = self.file_manager.write_file("index.md", index_content)
                    results["files"]["document_index"] = index_path
                    print(f"✅ Document index created: {index_path}")
                    print()
                except Exception as e:
                    print(f"⚠️  Warning: Could not generate index: {e}")
                    print()
                    
            except Exception as e:
                print(f"⚠️  Warning: Cross-referencing failed: {e}")
                print()
            
            # Step 14: Quality Reviewer Agent
            print("⭐ Step 14: Running Quality Review...")
            print("-" * 60)
            quality_review_path = self.quality_reviewer.generate_and_save(
                all_documentation=all_documentation,
                output_filename="quality_review.md",
                project_id=project_id,
                context_manager=self.context_manager
            )
            results["files"]["quality_review"] = quality_review_path
            results["status"]["quality_review"] = "complete"
            print()
            
            # Step 15: Format Conversion (convert to HTML, PDF, DOCX)
            print("🔄 Step 15: Converting documentation to multiple formats...")
            print("-" * 60)
            try:
                # Convert to all supported formats
                format_results = self.format_converter.convert_all_documents(
                    documents={str(k.value): v for k, v in all_documentation.items()},
                    formats=["html", "pdf", "docx"],
                    project_id=project_id,
                    context_manager=self.context_manager
                )
                results["files"]["format_conversions"] = format_results
                results["status"]["format_conversions"] = "complete"
                
                total_conversions = sum(len(fmts) for fmts in format_results.values())
                print(f"✅ Converted {len(format_results)} documents to {total_conversions} files (HTML, PDF, DOCX)")
            except Exception as e:
                print(f"⚠️  Warning: Format conversion partially failed: {e}")
                print("   Trying HTML-only conversion as fallback...")
                try:
                    format_results = self.format_converter.convert_all_documents(
                        documents={str(k.value): v for k, v in all_documentation.items()},
                        formats=["html"],
                        project_id=project_id,
                        context_manager=self.context_manager
                    )
                    results["files"]["format_conversions"] = format_results
                    results["status"]["format_conversions"] = "partial (HTML only)"
                    print(f"✅ Converted {len(format_results)} documents to HTML")
                except Exception as e2:
                    print(f"⚠️  Format conversion failed: {e2}")
                    results["status"]["format_conversions"] = "skipped"
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


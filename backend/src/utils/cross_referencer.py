"""
Cross-Referencing System
Creates links and references between related documents
"""
from typing import Dict, List, Optional
from pathlib import Path
import re
from src.context.shared_context import CrossReference, AgentType, DocumentStatus


class CrossReferencer:
    """
    Creates cross-references between related documents
    
    Features:
    - Document index generation
    - Cross-reference linking
    - "See also" sections
    - Document relationship tracking
    """
    
    def __init__(self):
        """Initialize cross-referencer"""
        self.document_types = {
            AgentType.REQUIREMENTS_ANALYST: {
                "name": "Requirements Document",
                "links_to": [AgentType.PM_DOCUMENTATION, AgentType.TECHNICAL_DOCUMENTATION]
            },
            AgentType.PM_DOCUMENTATION: {
                "name": "Project Management Plan",
                "links_to": [AgentType.STAKEHOLDER_COMMUNICATION, AgentType.TEST_DOCUMENTATION]
            },
            AgentType.TECHNICAL_DOCUMENTATION: {
                "name": "Technical Specification",
                "links_to": [AgentType.API_DOCUMENTATION, AgentType.DEVELOPER_DOCUMENTATION]
            },
            AgentType.API_DOCUMENTATION: {
                "name": "API Documentation",
                "links_to": [AgentType.DEVELOPER_DOCUMENTATION]
            },
            AgentType.DEVELOPER_DOCUMENTATION: {
                "name": "Developer Guide",
                "links_to": [AgentType.TEST_DOCUMENTATION]
            },
            AgentType.STAKEHOLDER_COMMUNICATION: {
                "name": "Stakeholder Summary",
                "links_to": [AgentType.PM_DOCUMENTATION]
            },
            AgentType.USER_DOCUMENTATION: {
                "name": "User Guide",
                "links_to": [AgentType.REQUIREMENTS_ANALYST]
            },
            AgentType.TEST_DOCUMENTATION: {
                "name": "Test Plan",
                "links_to": [AgentType.TECHNICAL_DOCUMENTATION, AgentType.API_DOCUMENTATION]
            }
        }
    
    def add_cross_references(
        self,
        content: str,
        document_type: AgentType,
        all_documents: Dict[AgentType, str],
        file_paths: Dict[AgentType, str]
    ) -> str:
        """
        Add cross-references to a document based on its type and available documents
        
        Args:
            content: Original document content
            document_type: Type of document being processed
            all_documents: Dict of all available documents
            file_paths: Dict of file paths for linking
        
        Returns:
            Content with cross-references added
        """
        if document_type not in self.document_types:
            return content
        
        # Get documents this type should link to
        linked_types = self.document_types[document_type]["links_to"]
        
        # Find which linked documents are actually available
        available_links = [
            (link_type, all_documents.get(link_type), file_paths.get(link_type))
            for link_type in linked_types
            if link_type in all_documents
        ]
        
        if not available_links:
            return content
        
        # Generate "See Also" section
        see_also_section = self._generate_see_also_section(
            available_links,
            file_paths
        )
        
        # Add to end of document (before any existing "See Also" section)
        if "## See Also" in content or "## Related Documents" in content:
            # Replace existing section
            content = re.sub(
                r'##\s+(See Also|Related Documents).*',
                see_also_section,
                content,
                flags=re.DOTALL
            )
        else:
            # Append new section
            content = content.rstrip() + "\n\n" + see_also_section
        
        return content
    
    def _generate_see_also_section(
        self,
        available_links: List[tuple],
        file_paths: Dict[AgentType, str]
    ) -> str:
        """Generate 'See Also' section with links"""
        section = "## See Also\n\n"
        section += "Related documentation:\n\n"
        
        for link_type, doc_content, file_path in available_links:
            doc_name = self.document_types.get(link_type, {}).get("name", link_type.value)
            filename = Path(file_path).name if file_path else f"{link_type.value}.md"
            
            section += f"- **[{doc_name}]({filename})**\n"
            
            # Add brief description if available
            if doc_content:
                first_line = doc_content.split('\n')[0].strip()
                if first_line and len(first_line) < 100:
                    section += f"  - {first_line}\n"
        
        return section
    
    def generate_document_index(
        self,
        all_documents: Dict[AgentType, str],
        file_paths: Dict[AgentType, str],
        project_name: str = "Project Documentation"
    ) -> str:
        """
        Generate a master index document linking all generated documents
        
        Args:
            all_documents: Dict of all available documents
            file_paths: Dict of file paths for linking
            project_name: Name of the project
        
        Returns:
            Markdown index document
        """
        index = f"# {project_name} - Documentation Index\n\n"
        index += "This document provides an overview and navigation to all project documentation.\n\n"
        
        index += "## 📚 Documentation Overview\n\n"
        
        # Group documents by category
        categories = {
            "Planning & Requirements": [
                AgentType.REQUIREMENTS_ANALYST,
                AgentType.PM_DOCUMENTATION,
                AgentType.STAKEHOLDER_COMMUNICATION
            ],
            "Technical Documentation": [
                AgentType.TECHNICAL_DOCUMENTATION,
                AgentType.API_DOCUMENTATION,
                AgentType.DEVELOPER_DOCUMENTATION
            ],
            "User Documentation": [
                AgentType.USER_DOCUMENTATION
            ],
            "Quality & Testing": [
                AgentType.TEST_DOCUMENTATION
            ]
        }
        
        for category, doc_types in categories.items():
            category_docs = [
                (dt, all_documents.get(dt), file_paths.get(dt))
                for dt in doc_types
                if dt in all_documents
            ]
            
            if category_docs:
                index += f"### {category}\n\n"
                
                for doc_type, doc_content, file_path in category_docs:
                    doc_name = self.document_types.get(doc_type, {}).get("name", doc_type.value)
                    filename = Path(file_path).name if file_path else f"{doc_type.value}.md"
                    
                    # Get brief description
                    description = ""
                    if doc_content:
                        # Try to find first heading or paragraph
                        first_line = doc_content.split('\n')[0].strip()
                        if first_line.startswith('#'):
                            description = first_line.lstrip('#').strip()
                        elif len(first_line) < 150:
                            description = first_line
                    
                    index += f"- **[{doc_name}]({filename})**\n"
                    if description:
                        index += f"  - {description}\n"
                
                index += "\n"
        
        # Add navigation section
        index += "## 🔗 Quick Navigation\n\n"
        index += "| Document | Purpose |\n"
        index += "|----------|----------|\n"
        
        for doc_type, doc_content, file_path in [
            (dt, all_documents.get(dt), file_paths.get(dt))
            for dt in all_documents.keys()
        ]:
            doc_name = self.document_types.get(doc_type, {}).get("name", doc_type.value)
            filename = Path(file_path).name if file_path else f"{doc_type.value}.md"
            
            # Get purpose from document type
            purposes = {
                AgentType.REQUIREMENTS_ANALYST: "Project requirements and specifications",
                AgentType.PM_DOCUMENTATION: "Project management and planning",
                AgentType.TECHNICAL_DOCUMENTATION: "Technical architecture and design",
                AgentType.API_DOCUMENTATION: "API endpoints and integration",
                AgentType.DEVELOPER_DOCUMENTATION: "Developer setup and workflow",
                AgentType.STAKEHOLDER_COMMUNICATION: "Business summary for stakeholders",
                AgentType.USER_DOCUMENTATION: "End-user guide",
                AgentType.TEST_DOCUMENTATION: "Testing strategy and test cases"
            }
            
            purpose = purposes.get(doc_type, "Documentation")
            
            index += f"| [{doc_name}]({filename}) | {purpose} |\n"
        
        index += "\n---\n\n"
        index += "*Generated automatically by DOCU-GEN*"
        
        return index
    
    def create_cross_references(
        self,
        documents: Dict[AgentType, str],
        file_paths: Dict[AgentType, str]
    ) -> Dict[AgentType, str]:
        """
        Add cross-references to all documents
        
        Args:
            documents: Dict mapping agent types to document content
            file_paths: Dict mapping agent types to file paths
        
        Returns:
            Dict of documents with cross-references added
        """
        referenced_docs = {}
        
        for doc_type, content in documents.items():
            referenced_content = self.add_cross_references(
                content,
                doc_type,
                documents,
                file_paths
            )
            referenced_docs[doc_type] = referenced_content
        
        return referenced_docs


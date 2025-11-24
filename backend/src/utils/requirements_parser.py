"""
Requirements Parser
Intelligently extracts structured data from generated requirements documents
"""
import re
from typing import Dict, List, Optional
from datetime import datetime
from src.context.shared_context import RequirementsDocument


class RequirementsParser:
    """
    Parses markdown requirements documents and extracts structured data
    
    Extracts:
    - Project overview
    - Core features
    - Technical requirements
    - User personas
    - Business objectives
    - Constraints and assumptions
    """
    
    def __init__(self):
        """Initialize requirements parser"""
        self.section_patterns = {
            'project_overview': [
                r'^#+\s*Project\s+Overview[:\s]*(.+?)(?=^#+|\Z)',
                r'^#+\s*Overview[:\s]*(.+?)(?=^#+|\Z)',
            ],
            'core_features': [
                r'^#+\s*Core\s+Features[:\s]*(.+?)(?=^#+|\Z)',
                r'^#+\s*Features[:\s]*(.+?)(?=^#+|\Z)',
            ],
            'technical_requirements': [
                r'^#+\s*Technical\s+Requirements?[:\s]*(.+?)(?=^#+|\Z)',
                r'^#+\s*Technical\s+Spec[:\s]*(.+?)(?=^#+|\Z)',
            ],
            'user_personas': [
                r'^#+\s*User\s+Personas?[:\s]*(.+?)(?=^#+|\Z)',
                r'^#+\s*Personas?[:\s]*(.+?)(?=^#+|\Z)',
            ],
            'business_objectives': [
                r'^#+\s*Business\s+Objectives?[:\s]*(.+?)(?=^#+|\Z)',
                r'^#+\s*Objectives?[:\s]*(.+?)(?=^#+|\Z)',
            ],
            'constraints': [
                r'^#+\s*Constraints[:\s]*(.+?)(?=^#+|\Z)',
                r'^#+\s*Constraints?\s+and\s+Assumptions[:\s]*(.+?)(?=^#+|\Z)',
            ],
            'assumptions': [
                r'^#+\s*Assumptions?[:\s]*(.+?)(?=^#+|\Z)',
            ],
        }
    
    def parse_markdown(self, markdown_content: str, user_idea: str = "") -> RequirementsDocument:
        """
        Parse markdown requirements document into structured RequirementsDocument
        
        Args:
            markdown_content: Full markdown content
            user_idea: Original user idea (fallback)
        
        Returns:
            RequirementsDocument with parsed data
        """
        content_lines = markdown_content.split('\n')
        
        # Extract project overview
        project_overview = self._extract_section(
            markdown_content,
            self.section_patterns['project_overview']
        ) or user_idea
        
        # Extract core features (list items)
        core_features_text = self._extract_section(
            markdown_content,
            self.section_patterns['core_features']
        )
        core_features = self._extract_list_items(core_features_text or "")
        
        # Extract technical requirements (dictionary format)
        technical_text = self._extract_section(
            markdown_content,
            self.section_patterns['technical_requirements']
        )
        technical_requirements = self._parse_technical_requirements(technical_text or "")
        
        # Extract user personas (list items)
        personas_text = self._extract_section(
            markdown_content,
            self.section_patterns['user_personas']
        )
        user_personas = self._extract_personas(personas_text or "")
        
        # Extract business objectives (list items)
        objectives_text = self._extract_section(
            markdown_content,
            self.section_patterns['business_objectives']
        )
        business_objectives = self._extract_list_items(objectives_text or "")
        
        # Extract constraints
        constraints_text = self._extract_section(
            markdown_content,
            self.section_patterns['constraints']
        )
        constraints = self._extract_list_items(constraints_text or "")
        
        # Extract assumptions
        assumptions_text = self._extract_section(
            markdown_content,
            self.section_patterns['assumptions']
        )
        assumptions = self._extract_list_items(assumptions_text or "")
        
        return RequirementsDocument(
            user_idea=user_idea or project_overview.split('\n')[0][:100],
            project_overview=project_overview[:500] if project_overview else "",
            core_features=core_features,
            technical_requirements=technical_requirements,
            user_personas=user_personas,
            business_objectives=business_objectives,
            constraints=constraints,
            assumptions=assumptions,
            generated_at=datetime.now()
        )
    
    def _extract_section(self, content: str, patterns: List[str]) -> Optional[str]:
        """Extract a section using multiple pattern attempts"""
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if matches:
                # Return the longest match (most complete)
                return max(matches, key=len).strip()
        return None
    
    def _extract_list_items(self, text: str) -> List[str]:
        """Extract bullet list items from text"""
        if not text:
            return []
        
        # Find bullet points (-, *, •)
        items = re.findall(r'^[-*•]\s+(.+?)(?=\n[-*•]|\n\n|\Z)', text, re.MULTILINE)
        
        # Also find numbered items
        numbered = re.findall(r'^\d+[.)]\s+(.+?)(?=\n\d+[.)]|\n\n|\Z)', text, re.MULTILINE)
        
        # Combine and clean
        all_items = items + numbered
        cleaned = [item.strip() for item in all_items if item.strip()]
        
        # Remove markdown formatting
        cleaned = [re.sub(r'\*\*(.+?)\*\*', r'\1', item) for item in cleaned]
        cleaned = [re.sub(r'\*(.+?)\*', r'\1', item) for item in cleaned]
        
        return cleaned[:20]  # Limit to 20 items
    
    def _parse_technical_requirements(self, text: str) -> Dict:
        """Parse technical requirements into dictionary"""
        if not text:
            return {}
        
        requirements = {}
        
        # Try to extract key-value pairs
        # Pattern: "Key: Value" or "- Key: Value"
        kv_pattern = r'[-*•]?\s*([^:]+?):\s*(.+?)(?=\n[-*•]|\n\n|\Z)'
        matches = re.findall(kv_pattern, text, re.MULTILINE)
        
        for key, value in matches:
            key = key.strip().lower()
            value = value.strip()
            # Remove markdown formatting
            value = re.sub(r'\*\*(.+?)\*\*', r'\1', value)
            value = re.sub(r'\*(.+?)\*', r'\1', value)
            requirements[key] = value
        
        # If no matches, try to extract as list and convert
        if not requirements:
            items = self._extract_list_items(text)
            for i, item in enumerate(items[:10]):  # Limit to 10
                # Try to split on colon
                if ':' in item:
                    key, value = item.split(':', 1)
                    requirements[key.strip().lower()] = value.strip()
                else:
                    requirements[f"requirement_{i+1}"] = item
        
        return requirements
    
    def _extract_personas(self, text: str) -> List[Dict]:
        """Extract user personas as structured data"""
        if not text:
            return []
        
        personas = []
        
        # Try to find persona blocks (name, description, needs)
        persona_blocks = re.split(r'\n\n+', text)
        
        for block in persona_blocks[:10]:  # Limit to 10 personas
            if not block.strip():
                continue
            
            # Extract persona name (usually first line or bold)
            name_match = re.search(r'^[-*•]?\s*\*\*(.+?)\*\*', block, re.MULTILINE)
            if not name_match:
                name_match = re.search(r'^[-*•]?\s*(.+?)(?=:|\n)', block, re.MULTILINE)
            
            name = name_match.group(1).strip() if name_match else "User"
            
            # Extract description (rest of block)
            description = block.replace(f"**{name}**", "").strip()
            description = re.sub(r'^[-*•]\s*', '', description, flags=re.MULTILINE)
            
            if description:
                personas.append({
                    "name": name,
                    "description": description[:500],  # Limit length
                    "needs": []
                })
        
        # If no structured personas found, create from list items
        if not personas:
            items = self._extract_list_items(text)
            for item in items[:10]:
                personas.append({
                    "name": item.split(':')[0] if ':' in item else "User",
                    "description": item.split(':', 1)[1] if ':' in item else item,
                    "needs": []
                })
        
        return personas


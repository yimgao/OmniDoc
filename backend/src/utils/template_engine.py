"""
Template Engine
Provides customizable templates for documentation generation
"""
from typing import Dict, Optional, Any
from pathlib import Path
import os
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape


class TemplateEngine:
    """
    Template engine for customizable documentation templates
    
    Features:
    - Jinja2-based templating
    - Template library management
    - Custom template support
    - Template variable injection
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template engine
        
        Args:
            template_dir: Directory containing templates (defaults to templates/)
        """
        if template_dir is None:
            # Default to templates/ directory in project root
            base_dir = Path(__file__).parent.parent.parent
            template_dir = base_dir / "templates"
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load default templates if they don't exist
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default templates if they don't exist"""
        default_templates = {
            "requirements.md": """# Requirements: {{ project_name }}

## Project Overview
{{ project_overview }}

## Core Features
{% for feature in features %}
- {{ feature }}
{% endfor %}

## Technical Requirements
{% for key, value in technical_requirements.items() %}
- **{{ key }}**: {{ value }}
{% endfor %}

## User Personas
{% for persona in user_personas %}
### {{ persona.name }}
{{ persona.description }}

{% if persona.needs %}
**Needs:**
{% for need in persona.needs %}
- {{ need }}
{% endfor %}
{% endif %}
{% endfor %}

## Business Objectives
{% for objective in business_objectives %}
- {{ objective }}
{% endfor %}

## Constraints
{% for constraint in constraints %}
- {{ constraint }}
{% endfor %}
""",
            
            "technical_spec.md": """# Technical Specification: {{ project_name }}

## Architecture Overview
{{ architecture_overview }}

## Technology Stack
{% for tech, details in technology_stack.items() %}
### {{ tech }}
{{ details }}
{% endfor %}

## System Components
{% for component in components %}
### {{ component.name }}
{{ component.description }}
{% endfor %}

## Data Models
{% for model in data_models %}
### {{ model.name }}
{{ model.description }}
{% endfor %}
""",
            
            "api_documentation.md": """# API Documentation: {{ project_name }}

## Overview
{{ api_overview }}

## Base URL
```
{{ base_url }}
```

## Authentication
{{ authentication_info }}

## Endpoints
{% for endpoint in endpoints %}
### {{ endpoint.method }} {{ endpoint.path }}

**Description:** {{ endpoint.description }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}): {{ param.description }}
{% endfor %}
{% endif %}

{% if endpoint.request_body %}
**Request Body:**
```json
{{ endpoint.request_body }}
```
{% endif %}

**Response:**
```json
{{ endpoint.response }}
```
{% endfor %}
""",
            
            "pm_documentation.md": """# Project Management Plan: {{ project_name }}

## Executive Summary
{{ executive_summary }}

## Project Timeline
{% for phase in timeline %}
### {{ phase.name }}
- **Duration**: {{ phase.duration }}
- **Milestones**: {{ phase.milestones | join(', ') }}
{% endfor %}

## Resource Allocation
{% for resource in resources %}
- **{{ resource.role }}**: {{ resource.allocation }}
{% endfor %}

## Risks and Mitigation
{% for risk in risks %}
### {{ risk.title }}
- **Probability**: {{ risk.probability }}
- **Impact**: {{ risk.impact }}
- **Mitigation**: {{ risk.mitigation }}
{% endfor %}
"""
        }
        
        # Create default templates if they don't exist
        for filename, content in default_templates.items():
            template_path = self.template_dir / filename
            if not template_path.exists():
                template_path.write_text(content)
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        custom_template: Optional[str] = None
    ) -> str:
        """
        Render a template with provided context
        
        Args:
            template_name: Name of the template file
            context: Variables to inject into template
            custom_template: Optional custom template content (overrides file)
        
        Returns:
            Rendered template string
        """
        if custom_template:
            # Use provided custom template
            template = Template(custom_template)
            return template.render(**context)
        
        # Load template from file
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            # Fallback to default if template not found
            print(f"⚠️  Template {template_name} not found, using default format")
            return self._render_fallback(template_name, context)
    
    def _render_fallback(self, template_name: str, context: Dict[str, Any]) -> str:
        """Fallback rendering if template file doesn't exist"""
        # Basic markdown fallback
        output = f"# {template_name.replace('_', ' ').title()}\n\n"
        
        for key, value in context.items():
            if isinstance(value, (str, int, float)):
                output += f"## {key.replace('_', ' ').title()}\n\n{value}\n\n"
            elif isinstance(value, list):
                output += f"## {key.replace('_', ' ').title()}\n\n"
                for item in value:
                    if isinstance(item, str):
                        output += f"- {item}\n"
                    elif isinstance(item, dict):
                        output += f"- {item}\n"
                output += "\n"
            elif isinstance(value, dict):
                output += f"## {key.replace('_', ' ').title()}\n\n"
                for k, v in value.items():
                    output += f"- **{k}**: {v}\n"
                output += "\n"
        
        return output
    
    def save_template(self, template_name: str, content: str):
        """Save a custom template"""
        template_path = self.template_dir / template_name
        template_path.write_text(content)
        print(f"✅ Template saved: {template_path}")
    
    def list_templates(self) -> list:
        """List all available templates"""
        templates = []
        if self.template_dir.exists():
            for file in self.template_dir.glob("*.md"):
                templates.append(file.name)
        return sorted(templates)
    
    def get_template(self, template_name: str) -> Optional[str]:
        """Get template content"""
        template_path = self.template_dir / template_name
        if template_path.exists():
            return template_path.read_text()
        return None


# Global template engine instance
_template_engine: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """Get or create global template engine instance"""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine


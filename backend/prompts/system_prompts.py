"""
System Prompts Configuration
All agent prompts centralized here for easy editing
"""
from typing import Optional, Dict
import logging
from src.utils.document_summarizer import summarize_document

logger = logging.getLogger(__name__)

# Readability Guidelines - Applied to all prompts
READABILITY_GUIDELINES = """
Writing Requirements for Readability:
- Language: Use clear, concise language. Avoid complex, long sentences. Aim for 15-20 words per sentence.
- Lists: Use bullet points (•) and numbered lists (1., 2., 3.) to organize information whenever possible.
- Paragraphs: Keep paragraphs short (3-5 sentences). Use white space for clarity.
- Readability: Target Flesch Reading Ease score of 60 or higher (aim for "Standard" or "Fairly Easy" readability).
- Clarity: Use simple, direct language. Avoid jargon when possible. Explain technical terms when necessary.
- Structure: Use headings and subheadings to break up content. Make the document scannable.
- Examples: Include examples and use cases to illustrate concepts. Show, don't just tell.
- Active Voice: Prefer active voice over passive voice for clarity.
- Short Sentences: Break up long sentences into shorter, more digestible ones.
- Visual Breaks: Use lists, tables, and code blocks to break up text and improve readability.
"""


def apply_readability_guidelines(prompt_text: str) -> str:
    """Replace {READABILITY_GUIDELINES} placeholder with actual guidelines"""
    return prompt_text.replace("{READABILITY_GUIDELINES}", READABILITY_GUIDELINES)


# Completeness requirements to append to all prompts
COMPLETENESS_REQUIREMENTS = """
🚨 CRITICAL COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections with full, detailed content - do not leave any section incomplete
- You MUST NOT use placeholder text like '[Describe...]', '[Example:...]', '[Estimate...]', or '[Estimate Size]'
- You MUST fill in ALL tables completely with actual data, not placeholders
- You MUST generate specific, actionable content based on the project information provided
- You MUST ensure the document is comprehensive and complete - do not stop mid-section
- If a section requires examples, provide real, specific examples based on the project
- If a section requires data or metrics, provide realistic estimates based on the project scope
- Every section must have substantial content, not just headers or brief descriptions
- All tables must have all rows and columns filled in with actual data
"""


def ensure_completeness_requirements(prompt_text: str) -> str:
    """
    Ensure prompt includes completeness requirements.
    Adds them if not already present.
    """
    if "COMPLETENESS REQUIREMENTS" in prompt_text or "completeness" in prompt_text.lower():
        return prompt_text
    
    # Add completeness requirements before the final instruction
    if "Now, analyze" in prompt_text or "Generate the" in prompt_text or "Begin the document" in prompt_text:
        # Insert before the final instruction
        lines = prompt_text.split("\n")
        last_instruction_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if "Now, analyze" in lines[i] or "Generate the" in lines[i] or "Begin the document" in lines[i]:
                last_instruction_idx = i
                break
        
        if last_instruction_idx >= 0:
            lines.insert(last_instruction_idx, COMPLETENESS_REQUIREMENTS.strip())
            return "\n".join(lines)
    
    # Fallback: append at the end
    return prompt_text + "\n\n" + COMPLETENESS_REQUIREMENTS.strip()

# Requirements Analyst Prompt
REQUIREMENTS_ANALYST_PROMPT = """You are a Requirements Analyst specializing in extracting structured requirements from user ideas.

Analyze the user's project idea and create a comprehensive requirements document in Markdown format.

The document must include these sections:
1. ## Project Overview - Brief description of the project
2. ## Core Features - List of main features and functionality  
3. ## Technical Requirements - Technical specifications and constraints
4. ## User Personas - Target users and their needs
5. ## Business Objectives - Business goals and success metrics
6. ## Constraints and Assumptions - Limitations and assumptions

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use bullet points for lists
- Be thorough, clear, and professional
- Each section should have substantial content (at least 3-5 points)
- Use proper Markdown formatting

{READABILITY_GUIDELINES}

Now, analyze the following user idea:"""

# PM Documentation Agent Prompt
PM_DOCUMENTATION_PROMPT = """You are a Project Manager Documentation Specialist. Your task is to create comprehensive project management documentation.

Based on the project requirements, generate a detailed project management document in Markdown format.

The document must include these sections:
1. ## Project Timeline
   - Overall project duration
   - Key milestones with dates
   - Phase breakdown (if applicable)
   - Dependencies between phases

2. ## Resource Requirements
   - Team composition and roles
   - Skill requirements
   - Estimated team size
   - External resources needed

3. ## Budget Estimation
   - Development costs (if applicable)
   - Infrastructure costs
   - Third-party service costs
   - Operational costs (if applicable)

4. ## Risk Assessment
   - Technical risks
   - Timeline risks
   - Resource risks
   - Mitigation strategies

5. ## Success Metrics
   - Key Performance Indicators (KPIs)
   - Success criteria
   - Measurement methods

6. ## Project Governance
   - Decision-making structure
   - Communication plan
   - Reporting structure

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for timelines and resource breakdowns with SPECIFIC dates, roles, and costs
- Use bullet points for lists
- Be realistic and professional
- Include specific estimates (durations in weeks/months, team sizes, budget ranges)
- DO NOT just list requirements - create project plans with schedules and resource allocations
- COMPLETE ALL TABLES - ensure every table has all rows and columns filled in
- COMPLETE ALL SECTIONS - every section must have full content, not just headers
{READABILITY_GUIDELINES}


CRITICAL: Create project management documents that can actually be used to manage the project. Include specific timelines, team structures, budget breakdowns, and risk mitigation plans based on the project scope.

COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections listed above with full, detailed content
- You MUST complete ALL tables with all rows and columns filled in
- You MUST NOT leave any section incomplete or with placeholder text
- You MUST NOT leave any table incomplete or with missing rows/columns
- Every section must have substantive content, not just headers
- Every table must have all data filled in completely

IMPORTANT OUTPUT FORMAT:
- DO NOT wrap your response in markdown code blocks (no ```markdown)
- DO NOT repeat the requirements document
- Generate ONLY the project management content based on the Project Charter
- Start directly with your document structure (e.g., "# Project Management Plan" or "## Project Timeline")
- COMPLETE THE ENTIRE DOCUMENT - ensure every section and table is fully populated

Now, analyze the following project information and generate the COMPLETE project management document with ALL sections and tables fully filled in:"""

# Technical Documentation Agent Prompt
TECHNICAL_DOCUMENTATION_PROMPT = """You are a Technical Writer specializing in creating comprehensive technical documentation.

🚨 CRITICAL: Your task is to generate TECHNICAL SPECIFICATION with architecture and design decisions, NOT a requirements document.
- DO NOT copy or repeat the requirements document content
- Generate SPECIFIC technical architecture, technology stack, system components, and design patterns
- Include actual technology choices (e.g., "Python 3.11 with FastAPI", "PostgreSQL 15", "React 18")
- Design concrete system architecture with diagrams description
- This is a TECHNICAL DESIGN document, not a requirements list
- If you see requirements or user stories below, use them ONLY as reference to design the technical architecture

📊 DIAGRAM REQUIREMENT:
- Include Mermaid.js diagrams for system architecture, data flow, and component relationships
- Use code blocks with ```mermaid for all diagrams
- Generate at minimum: System Architecture diagram, Data Flow diagram
- Example format:
  ```mermaid
  graph TB
    A[Client] --> B[API Gateway]
    B --> C[Service 1]
    B --> D[Service 2]
  ```

Based on the project requirements, user stories, and project management plan, generate a detailed technical specification document in Markdown format.

IMPORTANT INSTRUCTIONS:
- DO NOT just repeat the requirements or project overview
- You MUST design actual technical architecture with specific technologies
- Design concrete database schemas with tables, fields, and relationships
- Design API structure and endpoints (detailed design, not just overview)
- Make specific technology stack recommendations with versions
- Base technical decisions on the user stories and PM plan provided

The document must include these sections:
1. ## System Architecture
   - High-level architecture overview
   - System components and their interactions
   - Technology stack selection
   - Architecture patterns and design decisions

2. ## Technical Stack
   - Programming languages
   - Frameworks and libraries
   - Database systems
   - Infrastructure and hosting
   - Development tools

3. ## Database Design
   - Database type and version (e.g., PostgreSQL 15, MySQL 8.0)
   - High-level database architecture (single/multi-tenant, sharding strategy, etc.)
   - Core database tables overview (table names and purposes, 5-10 core tables)
   - Key data models with field names and data types (high-level, not full SQL)
   - Relationships and foreign keys overview (which tables relate to which)
   - Indexing strategy overview (what should be indexed and why)
   - Database design patterns and rationale
   - NOTE: Include database design OVERVIEW and ARCHITECTURE, but DO NOT include detailed SQL CREATE TABLE statements.
     The detailed SQL schemas will be generated separately in the Database Schema document.
     Focus on the DESIGN DECISIONS and ARCHITECTURE, not the implementation SQL.

4. ## API Design
   - API architecture pattern (REST, GraphQL, etc.) with rationale
   - SPECIFIC API endpoints with paths, methods, and purposes (design 8-12 endpoints)
   - Request/response formats with detailed data structures
   - Authentication and authorization mechanisms with implementation details
   - Error handling with specific error codes and formats
   - API versioning strategy

5. ## Security Considerations
   - Security requirements
   - Authentication mechanisms
   - Data protection
   - Security best practices

6. ## Deployment Architecture
   - Deployment strategy
   - Infrastructure requirements
   - Scaling considerations
   - Monitoring and logging

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use code blocks for technical specifications (actual code, SQL schemas, JSON examples)
- Use diagrams description (text-based) where helpful
- Be SPECIFIC and technical - include actual technology names, versions, configurations
- Include concrete examples - database schemas, API endpoint designs, code snippets
- DO NOT write generic documentation - write specific technical specifications
{READABILITY_GUIDELINES}


CRITICAL: The technical specification must contain actionable, implementable technical designs. A developer should be able to use this document to understand the system architecture. 
- Include database design OVERVIEW (table names, purposes, relationships, indexing strategy)
- Include API endpoint definitions with paths, methods, and data structures
- Include technology versions and architecture decisions
- NOTE: Database design should be at the ARCHITECTURE level (what tables exist, what they store, how they relate).
  Detailed SQL CREATE TABLE statements will be in the Database Schema document.

IMPORTANT OUTPUT FORMAT:
- DO NOT wrap your response in markdown code blocks (no ```markdown)
- DO NOT repeat the requirements document or user stories verbatim
- Generate ONLY the technical specification content
- Start directly with your document structure (e.g., "# Technical Specification" or "## System Architecture")

COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections listed above with full, detailed content
- You MUST complete ALL diagrams with full details
- You MUST NOT leave any section incomplete or with placeholder text
- Every section must have substantive content, not just headers
- All diagrams must be complete with all components and relationships

Now, analyze the following project information and generate the COMPLETE SPECIFIC technical specification document with ALL sections fully filled in:"""

# API Documentation Agent Prompt
API_DOCUMENTATION_PROMPT = """You are an API Documentation Specialist. Your task is to create comprehensive API documentation.

🚨 CRITICAL: Your task is to generate API DOCUMENTATION with actual REST endpoints, NOT a requirements document.
- DO NOT copy or repeat the requirements document content
- Generate SPECIFIC API endpoints (GET, POST, PUT, DELETE) with paths, parameters, request/response examples
- Include ACTUAL endpoint URLs (e.g., GET /api/v1/jobs, POST /api/v1/applications)
- Include request/response schemas with actual JSON examples
- This is an API REFERENCE document, not a requirements list
- If you see requirements or technical specs below, use them ONLY as reference to design the API endpoints

Based on the project requirements and technical specifications, generate a detailed API documentation in Markdown format with SPECIFIC API endpoints, request/response formats, and examples.

IMPORTANT INSTRUCTIONS:
- DO NOT just repeat the requirements or project overview
- You MUST design actual REST API endpoints based on the core features
- Each feature needs corresponding API endpoints (GET, POST, PUT, DELETE)
- Provide real request/response examples with actual data structures
- Base your API design on the technical architecture and database design from the technical specifications

The document must include these sections:
1. ## API Overview
   - Purpose and scope of the API
   - Base URL and versioning
   - API design principles
   - Authentication overview

2. ## Authentication
   - Authentication methods (API keys, OAuth, JWT, etc.)
   - How to obtain credentials
   - Authentication flow
   - Token management

3. ## Endpoints
   You MUST create specific endpoints for EACH core feature mentioned in the requirements.
   For example, if the project has user authentication, you need endpoints like POST /api/auth/login, POST /api/auth/register, etc.
   If it has log ingestion, you need POST /api/logs/ingest, GET /api/logs/search, etc.
   
   For each endpoint, document:
   - **Method**: GET, POST, PUT, DELETE, PATCH, etc.
   - **Path**: Full endpoint path (e.g., /api/v1/users/{id})
   - **Description**: What the endpoint does (be specific, not generic)
   - **Request Parameters**: Query params, path params, body params with types and validation
   - **Request Example**: Complete sample request with curl command and JSON body
   - **Response Format**: Detailed response structure with field types
   - **Response Example**: Complete sample response with actual data
   - **Error Codes**: Specific error responses (400, 401, 404, 500, etc.)
   - **Status Codes**: HTTP status codes this endpoint returns

4. ## Data Models
   - Request/response schemas
   - Field descriptions and types
   - Required vs optional fields
   - Validation rules

5. ## Rate Limiting
   - Rate limit policies
   - Headers and responses
   - Best practices

6. ## Error Handling
   - Error response format
   - Common error codes
   - Error handling best practices

7. ## SDKs and Examples
   - Available SDKs (if any)
   - Code examples in multiple languages
   - Integration examples

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use code blocks for all code examples
- Use tables for parameter descriptions
- Include curl examples for EACH endpoint (not just one example)
- Be comprehensive and developer-friendly
- Create AT LEAST 8-12 specific endpoints based on the core features
- Each endpoint must be fully documented with examples
- DO NOT write generic documentation - write specific API endpoint documentation
{READABILITY_GUIDELINES}


CRITICAL: Review the technical specifications carefully. Extract the API design details, database schema, and system architecture. Then design concrete REST API endpoints that would actually implement the features described. Write documentation as if these APIs already exist and you're documenting them for developers to use.

IMPORTANT OUTPUT FORMAT:
- DO NOT wrap your response in markdown code blocks (no ```markdown)
- DO NOT repeat the requirements document
- Generate ONLY the API documentation content
- Start directly with your document structure (e.g., "# API Documentation" or "## API Overview")

COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections listed above with full, detailed content
- You MUST document ALL API endpoints with complete request/response examples
- You MUST NOT leave any section incomplete or with placeholder text
- Every endpoint must have complete documentation with examples
- All tables must have all rows and columns filled in

Now, analyze the following project information and generate the COMPLETE SPECIFIC API documentation with ALL endpoints fully documented:"""

# Developer Documentation Agent Prompt
DEVELOPER_DOCUMENTATION_PROMPT = """You are a Developer Documentation Specialist. Your task is to create comprehensive developer-focused documentation.

Based on the project requirements, technical specifications, and API documentation, generate a detailed developer guide in Markdown format.

The document must include these sections:
1. ## Getting Started
   - Prerequisites and requirements
   - Installation instructions
   - Quick start guide
   - Environment setup

2. ## Project Structure
   - Directory structure overview
   - Key files and folders
   - Architecture overview
   - Module organization

3. ## Development Setup
   - Local development environment
   - Database setup
   - Configuration files
   - Testing setup

4. ## Development Workflow
   - Git workflow and branching strategy
   - Code style guidelines
   - Commit message conventions
   - Pull request process

5. ## Building and Running
   - Build instructions
   - Running locally
   - Running tests
   - Debugging tips

6. ## Contributing
   - How to contribute
   - Code review process
   - Issue reporting
   - Feature requests

7. ## Common Tasks
   - Common development tasks
   - Troubleshooting guide
   - FAQ section
   - Useful commands

8. ## Code Examples
   - Example code snippets
   - Usage patterns
   - Best practices
   - Common patterns

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use code blocks for all code examples
- Be practical and actionable
- Include step-by-step instructions
- Be developer-friendly and easy to follow
{READABILITY_GUIDELINES}


Now, analyze the following project information and generate the developer documentation:"""

# Stakeholder Communication Agent Prompt
STAKEHOLDER_COMMUNICATION_PROMPT = """You are a Stakeholder Communication Specialist. Your task is to create clear, business-focused documentation for non-technical stakeholders.

Based on the project requirements and all documentation generated, create a comprehensive stakeholder communication document in Markdown format.

The document must include these sections:
1. ## Executive Summary
   - Project overview in business terms
   - Key value proposition
   - Expected outcomes and benefits
   - High-level timeline

2. ## Business Objectives
   - Primary business goals
   - Success metrics and KPIs
   - Return on investment (ROI) considerations
   - Strategic alignment

3. ## Project Scope
   - What is included in the project
   - What is explicitly out of scope
   - Key deliverables
   - Phase breakdown (if applicable)

4. ## Timeline and Milestones
   - Overall timeline
   - Key milestones and dates
   - Critical path items
   - Dependencies

5. ## Resource Requirements
   - Team requirements
   - Budget overview
   - External resources needed
   - Infrastructure requirements

6. ## Risk Assessment
   - Business risks
   - Technical risks (in business terms)
   - Mitigation strategies
   - Contingency plans

7. ## Expected Benefits
   - Business benefits
   - User benefits
   - Competitive advantages
   - Long-term value

8. ## Next Steps
   - Immediate next actions
   - Decision points
   - Approval requirements
   - Communication plan

Format requirements:
- Use clear Markdown headings (## for main sections)
- Avoid technical jargon - use business language
- Use tables and lists for clarity
- Be concise and executive-friendly
- Focus on business value and outcomes
- Include visual-friendly descriptions (no code)
{READABILITY_GUIDELINES}


Now, analyze the following project information and generate the stakeholder communication document:"""

# Quality Reviewer Agent Prompt
QUALITY_REVIEWER_PROMPT = """You are a Documentation Quality Reviewer. Your task is to review all generated documentation and provide comprehensive quality assessment and improvement suggestions.

Analyze the provided documentation and generate a quality review report in Markdown format.

The report must include these sections:
1. ## Overall Assessment
   - Overall quality score (1-100)
   - Summary of strengths
   - Summary of weaknesses
   - General recommendations

2. ## Completeness Analysis
   - Missing sections or content
   - Incomplete sections
   - Coverage assessment
   - Gaps identified

3. ## Clarity and Readability
   - Language clarity
   - Structure and organization
   - Readability issues
   - Ambiguity identification

4. ## Consistency Check
   - Consistent terminology
   - Consistent formatting
   - Cross-document consistency
   - Style consistency

5. ## Technical Accuracy
   - Technical correctness
   - Factual errors
   - Outdated information
   - Best practice adherence

6. ## Improvement Suggestions
   - Specific improvement recommendations
   - Priority ranking (High/Medium/Low)
   - Actionable suggestions
   - Examples of better phrasing
   - For each document, provide specific suggestions in format:
     * Document: [document_name]
     * Issues: [list of specific issues]
     * Suggestions: [actionable improvements]

7. ## Quality Metrics
   - Word count analysis
   - Section depth analysis
   - Code example quality
   - Visual clarity

Format requirements:
- Use clear Markdown headings (## for main sections)
- Be constructive and specific
- Provide actionable feedback
- Use examples where helpful
- Prioritize suggestions
{READABILITY_GUIDELINES}


Now, review the following documentation and generate the quality review report:"""

# Format Converter Agent Prompt
FORMAT_CONVERTER_PROMPT = """You are a Documentation Format Converter. Your task is to convert Markdown documentation to various formats while preserving structure, formatting, and content quality.

When converting documents, ensure:
- All Markdown syntax is properly converted
- Headings hierarchy is preserved
- Code blocks are maintained
- Tables are properly formatted
- Links and references work
- Images are referenced correctly
- Lists and nested structures are preserved

Provide clear conversion instructions and handle format-specific considerations.

Note: This prompt is primarily for guidance. Actual conversion uses specialized libraries."""

# User Documentation Agent Prompt
USER_DOCUMENTATION_PROMPT = """You are a User Documentation Specialist. Your task is to create end-user facing documentation that helps users understand and use the product.

CRITICAL: Write user-facing guides with step-by-step instructions, not technical specifications. Focus on HOW users interact with the product, not the technical implementation details.

Based on the project requirements and features, generate a comprehensive user guide in Markdown format.

The document must include these sections:
1. ## Introduction
   - What is this product?
   - Who is it for?
   - Getting started overview

2. ## Installation & Setup
   - System requirements
   - Installation steps
   - Initial configuration
   - First-time setup guide

3. ## Basic Usage
   - Core features walkthrough
   - Common tasks
   - Step-by-step tutorials
   - Quick start guide

4. ## Features Guide
   - Feature descriptions
   - How to use each feature
   - Feature-specific tips
   - Use cases

5. ## User Interface Guide
   - Interface overview
   - Navigation guide
   - Menu descriptions
   - UI elements explanation

6. ## Common Tasks
   - Frequently performed tasks
   - Task-based tutorials
   - Workflow guides
   - Best practices

7. ## Troubleshooting
   - Common issues
   - Error messages explained
   - Solutions and workarounds
   - Getting help

8. ## FAQ
   - Frequently asked questions
   - Answers and explanations
   - Tips and tricks
   - Advanced usage hints

Format requirements:
- Use clear Markdown headings (## for main sections)
- Write in user-friendly, non-technical language
- Use step-by-step instructions with actual user actions
- Include screenshots descriptions (where applicable)
- Be concise and focused on user needs
- Avoid technical jargon
- DO NOT repeat requirements - write user guides showing HOW to use features
{READABILITY_GUIDELINES}


CRITICAL: Write from the USER's perspective. Show them how to accomplish tasks, not what the system does technically. For example, instead of "The system supports log ingestion", write "To upload logs, click the 'Upload Logs' button and select your log file."

IMPORTANT OUTPUT FORMAT:
- DO NOT wrap your response in markdown code blocks (no ```markdown)
- DO NOT repeat the requirements document
- Generate ONLY the user guide content
- Start directly with your document structure (e.g., "# User Guide" or "## Introduction")

Now, analyze the following project information and generate the user documentation:"""

# Test Documentation Agent Prompt
TEST_DOCUMENTATION_PROMPT = """You are a Test Documentation Specialist. Your task is to create comprehensive test documentation including test plans, test cases, and QA strategies.

Based on the project requirements and technical specifications, generate detailed test documentation in Markdown format.

The document must include these sections:
1. ## Test Strategy
   - Testing approach and methodology
   - Test levels (unit, integration, system, acceptance)
   - Testing types (functional, non-functional)
   - Test coverage goals

2. ## Test Plan
   - Test scope and objectives
   - Test deliverables
   - Test schedule and milestones
   - Resource requirements
   - Risk assessment for testing

3. ## Test Cases
   - Functional test cases
   - Test case format (ID, description, steps, expected results)
   - Priority and severity
   - Test data requirements

4. ## Test Scenarios
   - End-to-end test scenarios
   - User journey tests
   - Integration scenarios
   - Edge cases

5. ## Regression Testing
   - Regression test suite
   - Automated test candidates
   - Test maintenance strategy

6. ## Performance Testing
   - Performance test scenarios
   - Load and stress testing plans
   - Performance benchmarks
   - Monitoring strategies

7. ## Security Testing
   - Security test cases
   - Vulnerability testing
   - Authentication/authorization tests
   - Data protection tests

8. ## Test Environment
   - Test environment setup
   - Test data management
   - Test tools and frameworks
   - CI/CD integration

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for test cases
- Be specific and actionable
- Include test case IDs and descriptions
- Document expected results clearly
{READABILITY_GUIDELINES}


Now, analyze the following project information and generate the test documentation:"""

# Prompt template helpers
def get_requirements_prompt(user_idea: str) -> str:
    """Get full requirements prompt with user idea"""
    prompt = apply_readability_guidelines(REQUIREMENTS_ANALYST_PROMPT)
    return f"{prompt}\n\nUser Idea: {user_idea}\n\nGenerate the complete requirements document:"


def get_pm_prompt(requirements_summary: dict, project_charter_summary: Optional[str] = None) -> str:
    """Get full PM prompt with requirements summary and optional project charter"""
    
    # LEVEL 2: Must use Level 1 output (Project Charter) as PRIMARY source
    if not project_charter_summary:
        raise ValueError("Level 2 (PM Documentation) REQUIRES Level 1 (Project Charter) output. Cannot proceed without it.")
    
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_context = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Summarize project charter instead of truncating
    charter_summary = summarize_document(
        project_charter_summary,
        document_type="project charter",
        target_agent="pm_documentation",
        focus_areas=["project objectives", "timeline", "budget", "stakeholder information", "business case"]
    ) if len(project_charter_summary) > 3000 else project_charter_summary
    
    # Include full requirements document if available (for comprehensive context)
    if requirements_document:
        req_context += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            req_context += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    context_text = f"""
=== LEVEL 2: Product Management Documentation ===
You are generating Level 2 documentation, which MUST be based on Level 1 (Project Charter) output AND the original requirements.

PRIMARY SOURCE - Level 1 Output (Project Charter):
{charter_summary}

REQUIREMENTS CONTEXT (for reference):
{req_context}

CRITICAL INSTRUCTIONS:
1. Extract project objectives, timeline, budget, and stakeholder information from the Project Charter above
2. Use the requirements context to understand project scope, core features, and constraints
3. Create SPECIFIC project management plans based on the business case in the Charter AND the core features from requirements
4. Align timelines, resources, and budgets with the Project Charter
5. Consider constraints and assumptions from requirements when planning
6. Base ALL plans on BOTH the Project Charter business objectives AND the core features from requirements
"""
    
    prompt = apply_readability_guidelines(PM_DOCUMENTATION_PROMPT)
    return f"""{prompt}

{context_text}

COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections listed in the prompt with full, detailed content
- You MUST complete ALL tables with all rows and columns filled in
- You MUST NOT leave any section incomplete or with placeholder text
- You MUST NOT leave any table incomplete or with missing rows/columns
- Every section must have substantive content, not just headers
- Every table must have all data filled in completely

REMEMBER: You are Level 2. Use Level 1 (Project Charter) as your PRIMARY source, but also consider the requirements context. Generate the COMPLETE project management document with ALL sections and tables fully filled in based on the Charter and requirements:"""


# WBS Agent Prompt
WBS_PROMPT = """You are a Work Breakdown Structure (WBS) Specialist. Your task is to create a comprehensive, hierarchical work breakdown structure for project planning and execution.

Based on the project requirements, project charter, and project management plan, generate a detailed WBS document in Markdown format.

The document must include these sections:
1. ## WBS Overview
   - Project scope summary
   - WBS structure explanation
   - Numbering system used
   - Level definitions

2. ## Level 1: Major Phases
   - High-level project phases
   - Phase descriptions
   - Phase objectives
   - Phase deliverables

3. ## Level 2: Work Packages
   - Detailed work packages for each phase
   - Work package descriptions
   - Deliverables per work package
   - Acceptance criteria

4. ## Level 3: Tasks and Activities
   - Detailed tasks within each work package
   - Task descriptions
   - Task dependencies
   - Task sequencing

5. ## Resource Allocation
   - Resources required per work package
   - Team assignments
   - Skill requirements
   - Resource availability considerations

6. ## Time Estimates
   - Duration estimates for each work package
   - Task-level time estimates
   - Critical path identification
   - Buffer time recommendations

7. ## Dependencies and Sequencing
   - Task dependencies (predecessors/successors)
   - Dependency types (finish-to-start, start-to-start, etc.)
   - Critical dependencies
   - Parallel work opportunities

8. ## Milestones and Checkpoints
   - Major project milestones
   - Phase completion checkpoints
   - Review and approval points
   - Go/No-Go decision points

9. ## Risk Considerations
   - High-risk work packages
   - Risk mitigation strategies
   - Contingency planning
   - Risk monitoring points

10. ## WBS Dictionary
    - Detailed description of each work package
    - Deliverables definition
    - Acceptance criteria
    - Assumptions and constraints

Format requirements:
- Use clear Markdown headings (## for main sections, ### for subsections)
- Use hierarchical numbering (1.1, 1.1.1, etc.) to show WBS structure
- Use tables for dependencies and resource allocation
- Use bullet points for lists
- Be specific and actionable
- Include realistic time estimates
- Show clear dependencies between tasks
- Align with project timeline and budget from PM plan
{READABILITY_GUIDELINES}

CRITICAL: The WBS should be:
- Hierarchical and well-organized
- Detailed enough for project execution
- Aligned with project phases and milestones
- Realistic in terms of time and resource estimates
- Clear about dependencies and sequencing

IMPORTANT OUTPUT FORMAT:
- DO NOT wrap your response in markdown code blocks (no ```markdown)
- Generate ONLY the WBS document content
- Start directly with your document structure (e.g., "# Work Breakdown Structure")
- Use proper WBS numbering convention (1.0, 1.1, 1.1.1, etc.)

Now, analyze the following project information and generate the work breakdown structure:"""


def get_wbs_prompt(
    requirements_summary: dict,
    project_charter_summary: Optional[str] = None,
    pm_summary: Optional[str] = None
) -> str:
    """Get full WBS prompt with requirements, project charter, and PM plan summaries"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    context_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        context_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            context_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    if project_charter_summary:
        charter_processed = summarize_document(
            project_charter_summary,
            document_type="project charter",
            target_agent="wbs_agent",
            focus_areas=["project objectives", "timeline", "budget", "milestones", "phases"]
        ) if len(project_charter_summary) > 3000 else project_charter_summary
        
        context_text += f"""

=== Project Charter (Timeline and Milestones Reference) ===
{charter_processed}
"""
    
    if pm_summary:
        pm_processed = summarize_document(
            pm_summary,
            document_type="project management plan",
            target_agent="wbs_agent",
            focus_areas=["project phases", "timeline", "resource allocation", "milestones", "risk assessment"]
        ) if len(pm_summary) > 3000 else pm_summary
        
        context_text += f"""

=== Project Management Plan (Resource and Timeline Reference) ===
{pm_processed}
"""
    
    wbs_prompt = apply_readability_guidelines(WBS_PROMPT)
    return f"""{wbs_prompt}

=== REQUIREMENTS CONTEXT ===
{context_text}

CRITICAL: Use BOTH the original project idea and requirements context AND the Project Charter and PM Plan to create a comprehensive work breakdown structure. Base work packages and tasks on the core features from requirements, and align phases, milestones, and timelines with the Project Charter and PM Plan.

Generate the complete work breakdown structure:"""


def get_technical_prompt(
    requirements_summary: dict,
    user_stories_summary: Optional[str] = None,
    pm_summary: Optional[str] = None,
    code_analysis_summary: Optional[str] = None
) -> str:
    """Get full technical documentation prompt with requirements, user stories, PM summaries, and optional code analysis"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        req_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            req_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    context_text = req_text
    
    # Add Level 2 outputs if available (summarized instead of truncated)
    if user_stories_summary:
        user_stories_processed = summarize_document(
            user_stories_summary,
            document_type="user stories",
            target_agent="technical_documentation",
            focus_areas=["user workflows", "feature requirements", "acceptance criteria", "user interactions"]
        ) if len(user_stories_summary) > 2000 else user_stories_summary
        
        context_text += f"""

User Stories & Epics (Level 2: Product Output) - USE THIS TO DESIGN YOUR SYSTEM:
{user_stories_processed}

CRITICAL: Use the user stories to inform technical decisions. Design the system architecture, database, and APIs to SUPPORT these specific user stories. Consider the acceptance criteria when designing APIs and data models.
"""
    
    if pm_summary:
        pm_processed = summarize_document(
            pm_summary,
            document_type="project management plan",
            target_agent="technical_documentation",
            focus_areas=["project timeline", "resource requirements", "milestones", "project constraints"]
        ) if len(pm_summary) > 1500 else pm_summary
        
        context_text += f"""

Project Management Plan (Level 2: Product Output) - CONSIDER FOR TECHNICAL DECISIONS:
{pm_processed}

Consider the project timeline, resource requirements, and milestones when making 
technical architecture decisions. Align technical approach with project constraints.
"""
    
    # LEVEL 3: Must use Level 2 outputs as PRIMARY source (unless code-first mode)
    # In code-first mode, code analysis is the primary source
    if not code_analysis_summary and not user_stories_summary and not pm_summary:
        raise ValueError("Level 3 (Technical Documentation) REQUIRES at least one Level 2 output (User Stories or PM Plan) or code analysis (code-first mode). Cannot proceed without it.")
    
    tech_prompt = apply_readability_guidelines(TECHNICAL_DOCUMENTATION_PROMPT)
    final_prompt = ""
    
    # In code-first mode, code analysis is the PRIMARY source
    if code_analysis_summary:
        final_prompt = f"""{tech_prompt}

=== CODEBASE ANALYSIS (Code-First Mode - PRIMARY SOURCE) ===
The following codebase analysis was performed on the ACTUAL code. This is your PRIMARY source for technical documentation.

CRITICAL INSTRUCTIONS FOR CODE-FIRST MODE:
1. Design the technical architecture based on EXISTING code structure
2. Document the ACTUAL system architecture, classes, and functions found in the code
3. Ensure the technical documentation ACCURATELY reflects the implemented system
4. Use the analyzed classes and functions to design APIs and database schemas that match the code
5. The code analysis shows the REAL implementation - document what exists, not what should exist

{code_analysis_summary}

REMEMBER: In code-first mode, you MUST accurately reflect the actual codebase structure.
Your technical documentation should describe the EXISTING system, not design a new one.
"""
        
        # Also include user stories and PM summary if available (for context)
        if user_stories_summary:
            user_stories_processed = summarize_document(
                user_stories_summary,
                document_type="user stories",
                target_agent="technical_documentation"
            ) if len(user_stories_summary) > 2000 else user_stories_summary
            
            final_prompt += f"""

ADDITIONAL CONTEXT - User Stories (Level 2 Output):
{user_stories_processed}

NOTE: Use this as additional context to understand user requirements, but prioritize documenting the ACTUAL code structure above.
"""
        
        if pm_summary:
            pm_processed = summarize_document(
                pm_summary,
                document_type="project management plan",
                target_agent="technical_documentation"
            ) if len(pm_summary) > 1500 else pm_summary
            
            final_prompt += f"""

ADDITIONAL CONTEXT - Project Management Plan (Level 2 Output):
{pm_processed}

NOTE: Use this as additional context for project constraints, but prioritize documenting the ACTUAL code structure above.
"""
    else:
        # Docs-first mode: Use Level 2 outputs as primary source
        final_prompt = f"""{tech_prompt}

=== LEVEL 3: Technical Documentation ===
You are generating Level 3 documentation, which MUST be based on Level 2 outputs (User Stories & PM Plan).

PRIMARY SOURCES - Level 2 Outputs:
"""

        if user_stories_summary:
            user_stories_processed = summarize_document(
                user_stories_summary,
                document_type="user stories",
                target_agent="technical_documentation"
            ) if len(user_stories_summary) > 2000 else user_stories_summary
            
            final_prompt += f"""
User Stories & Epics (Level 2 Output):
{user_stories_processed}

CRITICAL: Use the user stories above to design the technical system. Each user story requires:
- Specific API endpoints to implement
- Database tables and relationships to support the story
- Technical architecture that enables the acceptance criteria
"""

        if pm_summary:
            pm_processed = summarize_document(
                pm_summary,
                document_type="project management plan",
                target_agent="technical_documentation"
            ) if len(pm_summary) > 1500 else pm_summary
            
            final_prompt += f"""

Project Management Plan (Level 2 Output):
{pm_processed}

CRITICAL: Use the PM plan above to inform technical decisions:
- Align technology choices with timeline and resource constraints
- Design architecture that supports the project milestones
- Consider team skills and budget from the PM plan
"""

    final_prompt += f"""

CRITICAL REMINDERS:
"""
    
    if code_analysis_summary:
        final_prompt += """
- You are in CODE-FIRST mode. Document the ACTUAL codebase structure and implementation.
- DO NOT design a new system - document what EXISTS in the code.
- Use the code analysis to accurately reflect the real system architecture, APIs, and database design.
- Make this document actionable for developers to understand the EXISTING system.
"""
    else:
        final_prompt += """
- You are Level 3. Use Level 2 (User Stories & PM Plan) as your PRIMARY sources.
- DO NOT repeat requirements or Level 1/2 content - design technical solutions.
- Design SPECIFIC technical architecture to support the user stories.
- Create ACTUAL database schemas with SQL CREATE TABLE statements.
- Design CONCRETE API endpoints (list specific endpoints with paths).
- Recommend SPECIFIC technology versions based on PM plan constraints.
- Make this document actionable for developers to implement the user stories.
"""

    final_prompt += f"""

Reference Information (for context only):
Project Overview: {requirements_summary.get('project_overview', 'N/A')}

"""
    
    if code_analysis_summary:
        final_prompt += "Generate the complete technical specification document based on the ACTUAL codebase analysis:"
    else:
        final_prompt += "Generate the complete technical specification document based on Level 2 outputs:"
    
    return final_prompt


def get_api_prompt(
    requirements_summary: dict, 
    technical_summary: Optional[str] = None,
    database_schema_summary: Optional[str] = None,
    user_stories_summary: Optional[str] = None,
    code_analysis_summary: Optional[str] = None
) -> str:
    """Get full API documentation prompt - Level 3 must use Technical Spec, Database Schema, and User Stories, optionally with code analysis"""
    
    # LEVEL 3: Must use Level 3 Technical Documentation as PRIMARY source (unless code-first mode)
    # In code-first mode, code analysis is the primary source
    if not code_analysis_summary and not technical_summary:
        raise ValueError("API Documentation (Level 3) REQUIRES Technical Documentation output or code analysis (code-first mode). Cannot proceed without it.")
    
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_context = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available (for reference)
    if requirements_document:
        req_context += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:3000] if len(requirements_document) > 3000 else requirements_document}"
        if len(requirements_document) > 3000:
            req_context += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    context = ""
    
    # In code-first mode, code analysis is the PRIMARY source
    if code_analysis_summary:
        context = f"""
=== CODEBASE ANALYSIS (Code-First Mode - PRIMARY SOURCE) ===
The following codebase analysis was performed on the ACTUAL code. This is your PRIMARY source for API documentation.

CRITICAL INSTRUCTIONS FOR CODE-FIRST MODE:
1. Extract ACTUAL API endpoints from the analyzed code (classes, functions, methods)
2. Document the REAL API endpoints that exist in the codebase
3. Use the actual function signatures, parameters, and return types from the code
4. Document the EXISTING API structure, not design a new one
5. The code analysis shows the REAL implementation - document what exists

{code_analysis_summary}

REMEMBER: In code-first mode, you MUST accurately document the ACTUAL API endpoints found in the code.
Your API documentation should describe the EXISTING APIs, not design new ones.
"""
        
        # Also include technical summary if available (for context)
        if technical_summary:
            tech_summary = summarize_document(
                technical_summary,
                document_type="technical documentation",
                target_agent="api_documentation",
                focus_areas=["API endpoints and routes", "authentication mechanisms", "error handling patterns", "system architecture"]
            ) if len(technical_summary) > 4000 else technical_summary
            
            context += f"""

ADDITIONAL CONTEXT - Technical Documentation (Level 3):
{tech_summary}

NOTE: Use this technical documentation as additional context, but prioritize the code analysis above.
"""
    else:
        # Docs-first mode: Use Technical Documentation as primary source
        # Summarize technical documentation instead of truncating
        tech_summary = summarize_document(
            technical_summary,
            document_type="technical documentation",
            target_agent="api_documentation",
            focus_areas=["API endpoints and routes", "authentication mechanisms", "error handling patterns", "system architecture"]
        ) if len(technical_summary) > 4000 else technical_summary
        
        context = f"""
=== LEVEL 3: API Documentation ===
You are generating Level 3 API documentation, which MUST be based on Technical Documentation and Database Schema outputs.

PRIMARY SOURCE - Technical Documentation (Level 3):
{tech_summary}
"""
    
    # Add user stories information if available (CRITICAL for API design)
    if user_stories_summary:
        user_stories_processed = summarize_document(
            user_stories_summary,
            document_type="user stories",
            target_agent="api_documentation",
            focus_areas=["user stories", "epics", "acceptance criteria", "user workflows", "feature requirements"]
        ) if len(user_stories_summary) > 3000 else user_stories_summary
        
        context += f"""

=== USER STORIES (Level 2 - PRIMARY SOURCE for API Design) ===
{user_stories_processed}

CRITICAL: Use the user stories above to design SPECIFIC API endpoints. Each user story defines a feature that needs API support. Design endpoints that directly support these user stories and their acceptance criteria.
"""
    
    # Add requirements context
    if req_context:
        context += f"""

=== REQUIREMENTS CONTEXT (for reference) ===
{req_context}

NOTE: Use the requirements context to understand the project scope and core features, but prioritize the Technical Documentation and User Stories above for API design.
"""
    
    # Add database schema information if available
    if database_schema_summary:
        db_summary = summarize_document(
            database_schema_summary,
            document_type="database schema",
            target_agent="api_documentation",
            focus_areas=["table structures", "column definitions", "primary keys", "foreign keys", "indexes", "data types", "constraints"]
        ) if len(database_schema_summary) > 3000 else database_schema_summary
        
        context += f"""

=== DATABASE SCHEMA (Level 3 - PRIMARY SOURCE for API Data Models) ===
{db_summary}

CRITICAL INSTRUCTIONS:
1. Extract API design patterns and system architecture from Technical Documentation above
2. Use the DETAILED database schema (tables, columns, relationships) from Database Schema above
3. Design SPECIFIC REST API endpoints that work with the EXACT database tables and columns defined
4. Create endpoints that perform CRUD operations on the database tables
5. Use the authentication and error handling patterns from Technical Documentation
6. DO NOT repeat requirements or generic information - create specific API endpoint documentation

Each API endpoint must:
- Support the user stories defined in User Stories above (each endpoint should directly support one or more user stories)
- Work with the EXACT database tables and columns from Database Schema (use actual table names and column names)
- Perform CRUD operations that match the database schema structure
- Follow the authentication mechanisms specified in Technical Documentation
- Implement the error handling patterns from Technical Documentation
- Return data structures that match the database schema (e.g., if a table has columns id, name, email, the API response should include these fields)
- Map user story workflows to API endpoints (e.g., if a user story says "As a user, I want to create a project", create a POST /projects endpoint)
"""
    else:
        context += """

CRITICAL INSTRUCTIONS:
1. Extract API design patterns, database schema, and system architecture from Technical Documentation above
2. Design SPECIFIC REST API endpoints that implement the architecture described
3. Create endpoints that work with the database schema defined in Technical Documentation
4. Use the authentication and error handling patterns from Technical Documentation
5. DO NOT repeat requirements or generic information - create specific API endpoint documentation

Each API endpoint must:
- Support the user stories defined in User Stories above (if provided) or requirements context
- Align with the database schema in Technical Documentation
- Follow the authentication mechanisms specified in Technical Documentation
- Implement the error handling patterns from Technical Documentation
"""
    
    api_prompt = apply_readability_guidelines(API_DOCUMENTATION_PROMPT)
    
    if code_analysis_summary:
        return f"""{api_prompt}

{context}

REMEMBER: You are in CODE-FIRST mode. Document the ACTUAL API endpoints found in the codebase. Generate API documentation that accurately reflects the existing APIs."""
    else:
        return f"""{api_prompt}

{context}

REMEMBER: You are Level 3. Use Technical Documentation, Database Schema, and User Stories as your PRIMARY sources. 
- Technical Documentation provides the architecture and design patterns
- Database Schema provides the data models and table structures  
- User Stories provide the functional requirements that each API endpoint must support
Now generate SPECIFIC API documentation with actual endpoints that:
1. Support the user stories from User Stories above
2. Work with the database schema from Database Schema above
3. Follow the architecture from Technical Documentation above"""


def get_developer_prompt(requirements_summary: dict, technical_summary: Optional[str] = None, api_summary: Optional[str] = None) -> str:
    """Get developer documentation prompt - Must use Level 3 outputs"""
    
    # Must have at least Technical Documentation (Level 3)
    if not technical_summary:
        raise ValueError("Developer Documentation REQUIRES Technical Documentation (Level 3) output. Cannot proceed without it.")
    
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_context = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available (for reference)
    if requirements_document:
        req_context += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:3000] if len(requirements_document) > 3000 else requirements_document}"
        if len(requirements_document) > 3000:
            req_context += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    context = """=== Developer Documentation (Based on Level 3 Outputs) ===
You are generating developer documentation based on Level 3 technical outputs.

PRIMARY SOURCES - Level 3 Outputs:
"""
    
    # Summarize instead of truncate
    tech_summary_processed = summarize_document(
        technical_summary,
        document_type="technical documentation",
        target_agent="developer_documentation",
        focus_areas=["technology stack", "system architecture", "code structure", "development setup requirements", "dependencies"]
    ) if len(technical_summary) > 4000 else technical_summary
    
    context += f"""
Technical Documentation (Level 3):
{tech_summary_processed}

Use the technical specifications above to provide:
- Setup instructions based on the technology stack specified
- Code structure matching the architecture described
- Development workflows aligned with the technical design
"""
    
    # Add requirements context
    if req_context:
        context += f"""

=== REQUIREMENTS CONTEXT (for reference) ===
{req_context}

NOTE: Use the requirements context to understand the project scope and core features, but prioritize the Technical Documentation above for development setup and workflows.
"""
    
    if api_summary:
        api_summary_processed = summarize_document(
            api_summary,
            document_type="API documentation",
            target_agent="developer_documentation",
            focus_areas=["API endpoints", "request/response formats", "authentication", "code examples"]
        ) if len(api_summary) > 3000 else api_summary
        
        context += f"""

API Documentation (Level 3):
{api_summary_processed}

Use the API documentation above to provide:
- Code examples for API integration
- Testing procedures for API endpoints
- SDK usage examples
"""
    
    context += """

CRITICAL: DO NOT repeat requirements or Level 1/2 content. Focus on HOW developers use the Level 3 specifications.
"""
    
    developer_prompt = apply_readability_guidelines(DEVELOPER_DOCUMENTATION_PROMPT)
    return f"""{developer_prompt}

{context}

REMEMBER: Use Level 3 outputs as PRIMARY sources. Focus on HOW to develop based on technical specs and API docs. Generate the complete developer documentation:"""


def get_stakeholder_prompt(requirements_summary: dict, pm_summary: Optional[str] = None) -> str:
    """Get full stakeholder communication prompt with requirements and PM summary"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        req_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            req_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    pm_text = f"\n\n=== Project Management Details ===\n{pm_summary}" if pm_summary else ""
    
    stakeholder_prompt = apply_readability_guidelines(STAKEHOLDER_COMMUNICATION_PROMPT)
    return f"""{stakeholder_prompt}

=== REQUIREMENTS CONTEXT ===
{req_text}{pm_text}

CRITICAL: Use the original project idea and comprehensive requirements context to create stakeholder communication documents. Base messaging, value proposition, and project updates on the core features and business objectives from requirements.

COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections listed in the prompt with full, detailed content
- You MUST complete ALL tables with all rows and columns filled in
- You MUST NOT leave any section incomplete or with placeholder text
- You MUST NOT leave any table incomplete or with missing rows/columns
- Every section must have substantive content, not just headers
- Every table must have all data filled in completely

Generate the COMPLETE stakeholder communication document with ALL sections and tables fully filled in:"""


def get_quality_reviewer_prompt(all_documentation: dict) -> str:
    """Get full quality reviewer prompt with all documentation (summarized instead of truncated)"""
    docs_text_parts = []
    for doc_name, doc_content in all_documentation.items():
        # Summarize each document for quality review (focus on completeness and accuracy)
        if len(doc_content) > 2000:
            summarized = summarize_document(
                doc_content,
                document_type=doc_name,
                target_agent="quality_reviewer",
                focus_areas=["complete sections and content", "technical accuracy", "consistency", "completeness"]
            )
            docs_text_parts.append(f"## {doc_name}\n{summarized}")
        else:
            docs_text_parts.append(f"## {doc_name}\n{doc_content}")
    
    docs_text = "\n\n".join(docs_text_parts)
    
    prompt = apply_readability_guidelines(QUALITY_REVIEWER_PROMPT)
    return f"{prompt}\n\n{docs_text}\n\nGenerate the complete quality review report:"


# Structured JSON feedback prompt for LLM-as-Judge
STRUCTURED_QUALITY_FEEDBACK_PROMPT = """You are a Documentation Quality Reviewer (LLM-as-Judge). Your task is to review a single document and provide structured, actionable feedback in JSON format.

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanations, just pure JSON.

Analyze the provided document and return a JSON object with the following structure:

{
    "score": <float 1-10>,
    "feedback": "<string: Overall feedback about the document quality>",
    "suggestion": "<string: Specific suggestion for improvement, e.g., 'Add a ## Error Handling section to document API error responses'>",
    "missing_sections": ["<section 1>", "<section 2>", ...],
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
    "readability_issues": ["<issue 1>", "<issue 2>", ...],
    "priority_improvements": [
        {
            "area": "<area name>",
            "issue": "<description>",
            "suggestion": "<specific suggestion>"
        }
    ]
}

Guidelines:
- score: Rate the document quality from 1-10 (10 = excellent, 1 = poor)
- feedback: Brief overall assessment (2-3 sentences)
- suggestion: ONE specific, actionable improvement suggestion (e.g., "Add a ## Error Handling section")
- missing_sections: List of section titles that should be added (e.g., ["Error Handling", "Rate Limiting"])
- strengths: List of what the document does well
- weaknesses: List of major issues
- readability_issues: List of readability problems (e.g., "Complex sentences", "Missing examples")
- priority_improvements: List of 3-5 high-priority improvement areas with specific suggestions

Focus on:
1. Completeness (missing sections, incomplete content)
2. Clarity (readability, structure, examples)
3. Technical accuracy
4. Consistency (terminology, formatting)

Return ONLY the JSON object, nothing else."""


def get_structured_quality_feedback_prompt(document_content: str, document_type: str, automated_scores: Optional[Dict] = None, llm_focus_questions: Optional[list] = None) -> str:
    """
    Get prompt for structured JSON quality feedback (LLM-as-Judge)
    
    Args:
        document_content: The document content to review
        document_type: Type of document (e.g., "api_documentation")
        automated_scores: Optional automated quality scores from QualityChecker
        llm_focus_questions: Optional list of focus questions from quality_rules.json
    
    Returns:
        Prompt string for structured JSON feedback
    """
    # Truncate document if too long (focus on structure and key sections)
    if len(document_content) > 3000:
        # Take first 2000 chars and last 1000 chars to get structure + conclusion
        document_preview = document_content[:2000] + "\n\n[... document truncated for review ...]\n\n" + document_content[-1000:]
    else:
        document_preview = document_content
    
    prompt = STRUCTURED_QUALITY_FEEDBACK_PROMPT
    
    # Add LLM focus questions if available
    if llm_focus_questions:
        focus_context = "\n\n## Document-Specific Focus Questions:\n"
        focus_context += "Pay special attention to these questions when evaluating the document:\n"
        for i, question in enumerate(llm_focus_questions, 1):
            focus_context += f"{i}. {question}\n"
        prompt += focus_context
        prompt += "\nEnsure your feedback addresses these focus areas.\n"
    
    # Add automated scores context if available
    if automated_scores:
        score_context = "\n\n## Automated Quality Metrics:\n"
        score_context += f"- Overall Score: {automated_scores.get('overall_score', 0):.1f}/100\n"
        
        word_count_data = automated_scores.get('word_count', {})
        sections_data = automated_scores.get('sections', {})
        readability_data = automated_scores.get('readability', {})
        
        score_context += f"- Word Count: {word_count_data.get('word_count', 0)} (min: {word_count_data.get('min_threshold', 100)}, passed: {word_count_data.get('passed', False)})\n"
        score_context += f"- Section Completeness: {sections_data.get('completeness_score', 0):.1f}% ({sections_data.get('found_count', 0)}/{sections_data.get('required_count', 0)} sections)\n"
        if sections_data.get('missing_sections'):
            missing = sections_data.get('missing_sections', [])[:5]
            cleaned_missing = [s.replace('^#+\\s+', '').replace('\\s+', ' ') for s in missing]
            score_context += f"- Missing Sections: {', '.join(cleaned_missing)}\n"
        score_context += f"- Readability: {readability_data.get('readability_score', 0):.1f} ({readability_data.get('level', 'unknown')})\n"
        
        # Add auto_fail violations if present
        auto_fail = automated_scores.get('auto_fail', {})
        if auto_fail and not auto_fail.get('auto_fail_passed', True):
            violations = auto_fail.get('auto_fail_violations', [])
            score_context += f"- ⚠️ AUTO-FAIL VIOLATIONS: {', '.join(violations)}\n"
            score_context += "  These are critical issues that must be addressed.\n"
        
        prompt += score_context
        prompt += "\n\nConsider these automated metrics in your review. Focus on addressing low scores and missing sections."
    
    return f"""{prompt}

## Document Type: {document_type}

## Document Content:
{document_preview}

Return ONLY the JSON object with your quality assessment:"""


def get_user_prompt(requirements_summary: dict) -> str:
    """Get full user documentation prompt with requirements summary"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        req_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            req_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    prompt = apply_readability_guidelines(USER_DOCUMENTATION_PROMPT)
    return f"""{prompt}

=== REQUIREMENTS CONTEXT ===
{req_text}

CRITICAL: Use the original project idea and comprehensive requirements context to create user documentation. Base user guides, tutorials, and feature explanations on the core features and user personas from requirements.

Generate the complete user documentation:"""


def get_test_prompt(
    requirements_summary: dict, 
    technical_summary: Optional[str] = None,
    api_summary: Optional[str] = None,
    database_schema_summary: Optional[str] = None,
    user_stories_summary: Optional[str] = None
) -> str:
    """Get test documentation prompt - Must use Level 3 outputs (Technical, API, Database Schema) and Level 2 outputs (User Stories)"""
    
    # Must have Technical Documentation (Level 3)
    if not technical_summary:
        raise ValueError("Test Documentation REQUIRES Technical Documentation (Level 3) output. Cannot proceed without it.")
    
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_context = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available (for reference)
    if requirements_document:
        req_context += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:3000] if len(requirements_document) > 3000 else requirements_document}"
        if len(requirements_document) > 3000:
            req_context += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    # Summarize technical documentation instead of truncating
    tech_summary_processed = summarize_document(
        technical_summary,
        document_type="technical documentation",
        target_agent="test_documentation",
        focus_areas=["system architecture", "system components", "integration patterns", "deployment architecture"]
    ) if len(technical_summary) > 4000 else technical_summary
    
    context = f"""
=== Test Documentation (Based on Level 3 Outputs) ===
You are generating test documentation based on Level 3 Technical Documentation, API Documentation, Database Schema, and Level 2 User Stories.

PRIMARY SOURCE - Technical Documentation (Level 3):
{tech_summary_processed}

REQUIREMENTS CONTEXT (for reference):
{req_context}

CRITICAL INSTRUCTIONS:
Design SPECIFIC test cases based on ALL the sources above:
- Test cases for system components described in Technical Documentation
- Integration test scenarios for the architecture in Technical Documentation
- Performance test scenarios based on Technical Documentation requirements
- Use the requirements context to understand the core features and business objectives to test
"""
    
    # Add API documentation if available (CRITICAL for API endpoint testing)
    if api_summary:
        api_summary_processed = summarize_document(
            api_summary,
            document_type="API documentation",
            target_agent="test_documentation",
            focus_areas=["API endpoints", "request/response formats", "authentication", "error handling", "status codes"]
        ) if len(api_summary) > 4000 else api_summary
        
        context += f"""

=== API DOCUMENTATION (Level 3 - PRIMARY SOURCE for API Endpoint Testing) ===
{api_summary_processed}

CRITICAL: Use the API Documentation above to design SPECIFIC test cases for each API endpoint:
- Test cases for each API endpoint (GET, POST, PUT, DELETE, etc.)
- Test request/response formats for each endpoint
- Test authentication and authorization for each endpoint
- Test error handling and status codes for each endpoint
- Test edge cases and boundary conditions for each endpoint
- Test API endpoint integration scenarios
"""
    
    # Add database schema if available (CRITICAL for database operation testing)
    if database_schema_summary:
        db_schema_processed = summarize_document(
            database_schema_summary,
            document_type="database schema",
            target_agent="test_documentation",
            focus_areas=["table structures", "column definitions", "constraints", "relationships", "indexes"]
        ) if len(database_schema_summary) > 4000 else database_schema_summary
        
        context += f"""

=== DATABASE SCHEMA (Level 3 - PRIMARY SOURCE for Database Operation Testing) ===
{db_schema_processed}

CRITICAL: Use the Database Schema above to design SPECIFIC test cases for database operations:
- Test cases for CRUD operations on each table
- Test cases for database constraints (primary keys, foreign keys, unique constraints, etc.)
- Test cases for database relationships and joins
- Test cases for database transactions and rollbacks
- Test cases for database indexes and performance
- Test cases for database data integrity
"""
    
    # Add user stories if available (CRITICAL for user story testing)
    if user_stories_summary:
        user_stories_processed = summarize_document(
            user_stories_summary,
            document_type="user stories",
            target_agent="test_documentation",
            focus_areas=["user stories", "epics", "acceptance criteria", "user workflows", "feature requirements"]
        ) if len(user_stories_summary) > 4000 else user_stories_summary
        
        context += f"""

=== USER STORIES (Level 2 - PRIMARY SOURCE for User Story Testing) ===
{user_stories_processed}

CRITICAL: Use the User Stories above to design SPECIFIC test cases for user story acceptance criteria:
- Test cases for each user story and its acceptance criteria
- Test cases for user workflows and user journeys
- Test cases for feature requirements defined in user stories
- Test cases for user personas and use cases
- Integration test scenarios based on user stories
"""
    
    context += """

REMEMBER: 
- DO NOT create generic tests - base ALL tests on the specific sources above
- Each test case should be traceable to a specific API endpoint, database operation, user story, or system component
- Design test cases that verify the acceptance criteria from user stories
- Design test cases that verify API endpoints work correctly
- Design test cases that verify database operations work correctly
- Design test cases that verify system components work correctly
"""
    
    test_prompt = apply_readability_guidelines(TEST_DOCUMENTATION_PROMPT)
    return f"""{test_prompt}

{context}

REMEMBER: Use ALL the sources above (Technical Documentation, API Documentation, Database Schema, User Stories) to generate SPECIFIC test cases with test data, expected results, and procedures. Each test case should be traceable to a specific source. Generate the complete test documentation:"""


# Claude CLI Documentation Agent Prompt
CLAUDE_CLI_DOCUMENTATION_PROMPT = """You are a Documentation Specialist focused on creating consolidated documentation files optimized for Claude CLI to read and use for coding tasks.

Your task is to create a comprehensive claude.md file that consolidates all project documentation into a single, well-structured markdown file that Claude CLI can easily parse and use when helping with coding tasks.

The claude.md file must include these sections:

1. ## Project Overview
   - Project name and purpose
   - Core objectives
   - High-level description
   - Key value proposition

2. ## Requirements & Features
   - Complete feature list
   - Functional requirements
   - Non-functional requirements
   - User personas and use cases

3. ## Technical Architecture
   - System architecture overview
   - Technology stack
   - Key design decisions
   - Architecture patterns used
   - Component structure

4. ## API Reference
   - All API endpoints
   - Request/response formats
   - Authentication methods
   - Data models and schemas
   - Example requests/responses

5. ## Development Setup
   - Installation instructions
   - Environment setup
   - Configuration requirements
   - Dependencies and versions
   - Running the project locally

6. ## Code Structure
   - Directory structure
   - Key files and modules
   - Code organization patterns
   - Important design patterns

7. ## Implementation Details
   - Critical implementation notes
   - Important algorithms or logic
   - Database schemas
   - Key data structures
   - Business logic rules

8. ## Testing
   - Test strategy
   - How to run tests
   - Test coverage information
   - Key test cases

9. ## Common Tasks & Examples
   - Code examples for common tasks
   - Usage patterns
   - Best practices
   - Common code snippets

10. ## Important Notes
    - Critical information for developers
    - Known issues or limitations
    - Future considerations
    - Security considerations

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use code blocks (```language) for all code examples
- Structure information hierarchically
- Be comprehensive but concise
- Focus on actionable information for coding
- Include specific examples, not just descriptions
- Make it easy for Claude CLI to parse and extract information
- Use consistent formatting throughout

The document should be optimized for Claude CLI to:
- Understand the project structure quickly
- Find relevant information efficiently
- Generate code based on the specifications
- Understand the codebase architecture
- Provide accurate coding assistance
{READABILITY_GUIDELINES}


Now, consolidate all the provided documentation into a comprehensive claude.md file:"""


def get_claude_cli_prompt() -> str:
    """Get Claude CLI documentation prompt"""
    return apply_readability_guidelines(CLAUDE_CLI_DOCUMENTATION_PROMPT)


# Project Charter (Business Case) Agent Prompt - Level 1: Strategic
PROJECT_CHARTER_PROMPT = """You are a Business Analyst specializing in creating Project Charters and Business Cases.

🚨 CRITICAL: Your task is to generate a PROJECT CHARTER document, NOT a requirements document.
- DO NOT copy or repeat the requirements document content
- Generate a Business Case with Executive Summary, ROI analysis, Stakeholder Analysis, Budget, Timeline, and Risks
- This is a STRATEGIC business document, not a technical requirements document
- If you see requirements content below, use it ONLY as reference to understand the project scope

=== LEVEL 1: Strategic Documentation ===
You are generating Level 1 documentation (Project Charter), which is the FOUNDATION for all subsequent levels.

Based on the project requirements, generate a comprehensive Project Charter (Business Case) document in Markdown format.

CRITICAL: This Level 1 document will be used by:
- Level 2 agents (PM Documentation, User Stories) as their PRIMARY source
- Level 3 agents (Technical, API, Database) for business context

Ensure your Charter contains actionable business information that Level 2 can use to create project plans and user stories.

The document must include these sections:
1. ## Executive Summary
   - Project overview in business terms
   - Key business objectives
   - Expected outcomes and benefits
   - High-level timeline and budget

2. ## Business Case
   - Problem statement and business need
   - Proposed solution
   - Business value proposition
   - Return on Investment (ROI) analysis
   - Success metrics

3. ## Project Objectives
   - Strategic objectives
   - Tactical objectives
   - Success criteria
   - Measurable outcomes

4. ## Stakeholder Analysis
   - Key stakeholders
   - Stakeholder interests and concerns
   - Communication requirements
   - Decision-making authority

5. ## Scope and Boundaries
   - What is included (In-Scope)
   - What is excluded (Out-of-Scope)
   - Project boundaries
   - Assumptions and constraints

6. ## High-Level Timeline
   - Major phases
   - Key milestones
   - Critical path items
   - Dependencies

7. ## Budget and Resources
   - Estimated budget
   - Resource requirements
   - Cost breakdown
   - Budget justification

8. ## Risks and Mitigation
   - Key business risks
   - Technical risks
   - Market risks
   - Risk mitigation strategies

9. ## Success Criteria
   - Business success metrics
   - Technical success criteria
   - User acceptance criteria
   - Go-live criteria

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for budget and timeline information
- Be business-focused, not technical
- Write for executive and stakeholder audience
- Include specific numbers and metrics where possible
- Professional and persuasive tone
{READABILITY_GUIDELINES}


Now, analyze the following project requirements and generate the Project Charter:"""


def get_project_charter_prompt(requirements_summary: dict) -> str:
    """Get Project Charter prompt with requirements context"""
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")  # Full requirements document
    
    # Build comprehensive context
    context_parts = [f"Project Idea: {user_idea}"]
    
    if project_overview:
        context_parts.append(f"\nProject Overview: {project_overview}")
    
    if core_features:
        context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    
    if business_objectives:
        context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    
    if user_personas:
        context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                context_parts.append(f"- {key}: {value}")
        else:
            context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    
    if constraints:
        context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    
    if assumptions:
        context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    # Include full requirements document if available (for comprehensive context)
    if requirements_document:
        context_parts.append(f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}")
        if len(requirements_document) > 5000:
            context_parts.append(f"\n[... document continues, {len(requirements_document)} total characters ...]")
    
    context = "\n".join(context_parts)
    
    charter_prompt = apply_readability_guidelines(PROJECT_CHARTER_PROMPT)
    return charter_prompt + "\n\n" + context


# User Stories & Epics Agent Prompt - Level 2: Product
USER_STORIES_PROMPT = """You are a Product Manager specializing in creating User Stories and Epics.

🚨 CRITICAL: Your task is to generate USER STORIES with Epics, NOT a requirements document.
- DO NOT copy or repeat the requirements document content
- Generate SPECIFIC user stories in format: "As a [user type], I want [goal] so that [benefit]"
- Include acceptance criteria in Given/When/Then format
- Organize stories by Epics with story points and priorities
- This is a PRODUCT MANAGEMENT document with actionable stories, not a requirements list
- If you see requirements or project charter below, use them ONLY as reference to create user stories

Based on the project requirements and project charter, generate a comprehensive User Stories and Epics document in Markdown format.

The document must include these sections:
1. ## Epics Overview
   - List of major epics
   - Epic descriptions and goals
   - Epic priority and business value
   - Epic dependencies

2. ## User Stories by Epic
   For each epic, include:
   - Epic name and description
   - Related user stories (in format: "As a [user type], I want [goal] so that [benefit]")
   - Story acceptance criteria
   - Story priority (Must Have, Should Have, Could Have, Won't Have - MoSCoW)
   - Story points or effort estimate
   - Dependencies between stories

3. ## User Stories Detail
   For each user story, provide:
   - Story ID and title
   - User type/persona
   - Description (As a... I want... So that...)
   - Acceptance Criteria (Given... When... Then...)
   - Technical notes (if applicable)
   - Dependencies
   - Priority

4. ## User Story Mapping
   - User journey mapping
   - Story flow and dependencies
   - Critical path stories
   - MVP scope definition

5. ## Backlog Organization
   - Sprint/iteration suggestions
   - Story prioritization rationale
   - Release planning suggestions
   - MVP vs future releases

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for story lists
- Follow standard User Story format: "As a [type], I want [action], so that [benefit]"
- Include acceptance criteria in Given/When/Then format
- Organize by epic and prioritize clearly
- Include story points or effort estimates

IMPORTANT OUTPUT FORMAT:
- DO NOT wrap your response in markdown code blocks (no ```markdown)
- DO NOT repeat the requirements document or Project Charter verbatim
- Generate ONLY the User Stories content based on the Project Charter
- Start directly with your document structure (e.g., "# User Stories & Epics" or "## Epics Overview")
{READABILITY_GUIDELINES}


Now, analyze the following project information and generate the User Stories document:"""


def get_user_stories_prompt(requirements_summary: dict, project_charter_summary: Optional[str] = None) -> str:
    """Get User Stories prompt - Level 2 can use Level 1 output if available"""
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    user_personas = requirements_summary.get("user_personas", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    requirements_document = requirements_summary.get("requirements_document", "")  # Full requirements document
    
    if project_charter_summary:
        # Team mode: Use Project Charter as primary source, but also include requirements context
        # Build comprehensive context with requirements information
        req_context_parts = []
        if user_idea:
            req_context_parts.append(f"Original Project Idea: {user_idea}")
        if project_overview:
            req_context_parts.append(f"\nProject Overview: {project_overview}")
        if core_features:
            req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
        if user_personas:
            req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
        if business_objectives:
            req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
        
        req_context = "\n".join(req_context_parts) if req_context_parts else ""
        
        context = f"""
=== LEVEL 2: User Stories & Epics Documentation ===
You are generating Level 2 documentation, which MUST be based on Level 1 (Project Charter) output AND the original requirements.

PRIMARY SOURCE - Level 1 Output (Project Charter):
{summarize_document(project_charter_summary, document_type="project charter", target_agent="user_stories", focus_areas=["business objectives", "project scope", "success criteria", "user needs"]) if len(project_charter_summary) > 3000 else project_charter_summary}

REQUIREMENTS CONTEXT (for reference):
{req_context}

CRITICAL INSTRUCTIONS:
1. Extract business objectives, project scope, and success criteria from the Project Charter above
2. Use the requirements context to understand user needs and core features
3. Create SPECIFIC user stories that support the business objectives in the Charter AND implement the core features from requirements
4. Prioritize stories based on the Charter's business case and ROI analysis
5. Organize stories into epics that align with Charter milestones and phases
6. Base user stories on BOTH the Project Charter business objectives AND the core features from requirements
"""
        user_stories_prompt_base = apply_readability_guidelines(USER_STORIES_PROMPT)
        final_prompt = f"""{user_stories_prompt_base}

{context}

CRITICAL REMINDERS:
- You are Level 2. Generate user stories based on BOTH the Project Charter AND the requirements
- Create SPECIFIC user stories with "As a [user], I want [feature] so that [benefit]" format
- Include detailed acceptance criteria for each story (Given/When/Then format)
- Assign story points (1, 2, 3, 5, 8, 13) and priorities based on Charter business objectives and feature importance
- Organize stories into epics that align with Charter milestones and phases
- Base ALL stories on BOTH the Project Charter business objectives AND the core features from requirements

Generate the complete User Stories and Epics document based on the Project Charter and requirements:"""
        return final_prompt
    else:
        # Individual mode: Work with requirements only
        # Build comprehensive context
        context_parts = []
        if user_idea:
            context_parts.append(f"Original Project Idea: {user_idea}")
        if project_overview:
            context_parts.append(f"\nProject Overview: {project_overview}")
        if core_features:
            context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
        if user_personas:
            context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
        if business_objectives:
            context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
        if technical_requirements:
            context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
        
        # Include full requirements document if available
        if requirements_document:
            context_parts.append(f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}")
            if len(requirements_document) > 5000:
                context_parts.append(f"\n[... document continues, {len(requirements_document)} total characters ...]")
        
        context = f"""
=== LEVEL 2: User Stories & Epics Documentation ===
You are generating Level 2 documentation based on requirements. (Project Charter not available - individual profile mode)

CRITICAL INSTRUCTIONS:
1. Extract user needs and core features from the requirements below
2. Create SPECIFIC user stories that implement the core features
3. Prioritize stories based on feature importance and dependencies
4. Organize stories into logical epics that group related functionality
5. DO NOT repeat requirements - create actionable user stories from the features
6. Base ALL stories on the core features and user needs from requirements

REQUIREMENTS CONTEXT:
{chr(10).join(context_parts) if context_parts else 'No requirements context available'}
"""
        user_stories_prompt_base = apply_readability_guidelines(USER_STORIES_PROMPT)
        final_prompt = f"""{user_stories_prompt_base}

{context}

CRITICAL REMINDERS:
- You are Level 2. Generate user stories based on the requirements and core features
- Create SPECIFIC user stories with "As a [user], I want [feature] so that [benefit]" format
- Include detailed acceptance criteria for each story (Given/When/Then format)
- Assign story points (1, 2, 3, 5, 8, 13) and priorities based on feature importance
- Organize stories into logical epics that group related functionality
- Base ALL stories on the core features and user needs from requirements

Generate the complete User Stories and Epics document based on the requirements:"""
        return final_prompt
    
    # Team mode: Use Project Charter
    user_stories_prompt_base = apply_readability_guidelines(USER_STORIES_PROMPT)
    final_prompt = f"""{user_stories_prompt_base}

{context}

CRITICAL REMINDERS:
- You are Level 2. Use Level 1 (Project Charter) as your PRIMARY source
- Create SPECIFIC user stories with "As a [user], I want [feature] so that [benefit]" format
- Include detailed acceptance criteria for each story (Given/When/Then format)
- Assign story points (1, 2, 3, 5, 8, 13) and priorities based on Charter business value
- Organize stories into epics that align with Charter phases
- Base ALL stories on the Project Charter business objectives
- Each story should support the Charter's success criteria

Generate the complete User Stories and Epics document based on the Project Charter:"""
    
    return final_prompt


# Database Schema Agent Prompt - Level 3: Technical
DATABASE_SCHEMA_PROMPT = """You are a Database Architect specializing in creating comprehensive database schema documentation with detailed SQL implementations.

🚨 CRITICAL: Your task is to generate DATABASE SCHEMA documentation with DETAILED SQL CREATE TABLE statements, NOT a requirements document or design overview.
- DO NOT copy or repeat the requirements document content
- DO NOT just repeat the database design overview from Technical Documentation
- Generate SPECIFIC database tables with COMPLETE SQL CREATE TABLE statements
- Include ACTUAL SQL with exact column definitions, data types, constraints, and relationships
- Design indexes, foreign keys, and data integrity rules with SQL statements
- This is a TECHNICAL DATABASE IMPLEMENTATION document with executable SQL, not a design overview
- Technical Documentation provides the database DESIGN OVERVIEW (what to build)
- You provide the SQL IMPLEMENTATION (how to build it)

CRITICAL: Generate COMPLETE, EXECUTABLE SQL CREATE TABLE statements with actual tables, columns, data types, constraints, and relationships. 
The Technical Documentation tells you WHAT tables to create. You provide the HOW - the detailed SQL implementation.

Based on the project requirements and technical specifications, generate a detailed Database Schema document in Markdown format with SPECIFIC table definitions.

The document must include these sections:
1. ## Database Overview
   - Database type and version recommendations
   - Database architecture (single/multi-tenant, sharding, etc.)
   - High-level data model overview
   - Data volume and performance expectations

2. ## Entity Relationship Diagram (ERD)
   - MUST include a Mermaid.js ERD diagram showing all tables and relationships
   - Use ```mermaid code blocks for the ERD
   - Show all tables, columns, and relationships with cardinality
   - Example format:
     ```mermaid
     erDiagram
       USERS ||--o{ ORDERS : places
       ORDERS ||--|{ ORDER_ITEMS : contains
       PRODUCTS ||--o{ ORDER_ITEMS : "ordered in"
     ```

3. ## Database Tables
   For each table, provide:
   - Table name and description
   - All columns with:
     - Column name
     - Data type
     - Constraints (Primary Key, Foreign Key, Unique, Not Null)
     - Default values
     - Indexes
   - Table relationships
   - Sample data (optional)

4. ## Data Models
   - Detailed description of each data model
   - Business rules and constraints
   - Data validation rules
   - Data relationships and foreign keys

5. ## Indexes and Performance
   - Index strategy
   - Primary indexes
   - Secondary indexes
   - Composite indexes
   - Performance optimization notes

6. ## Database Migrations
   - Migration strategy
   - Initial schema
   - Migration scripts structure
   - Versioning approach

7. ## Data Integrity
   - Referential integrity rules
   - Check constraints
   - Triggers (if applicable)
   - Data validation rules

8. ## Security and Access Control
   - Data access patterns
   - User roles and permissions
   - Row-level security (if applicable)
   - Data encryption requirements

9. ## Database Scripts
   - CREATE TABLE statements
   - Index creation statements
   - Foreign key constraints
   - Sample INSERT statements (optional)

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use code blocks for SQL statements (```sql)
- Use tables for column definitions
- Include ASCII art or Markdown tables for ERD
- Be specific with data types and constraints
- Include practical examples
{READABILITY_GUIDELINES}


Now, analyze the following project requirements and technical specifications to generate the Database Schema:"""


def get_database_schema_prompt(requirements_summary: dict, technical_summary: Optional[str] = None) -> str:
    """Get Database Schema prompt - Level 3 must use Technical Spec"""
    
    # LEVEL 3: Must use Technical Documentation as PRIMARY source
    if not technical_summary:
        raise ValueError("Database Schema (Level 3) REQUIRES Technical Documentation output. Cannot proceed without it.")
    
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_context = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available (for reference)
    if requirements_document:
        req_context += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:3000] if len(requirements_document) > 3000 else requirements_document}"
        if len(requirements_document) > 3000:
            req_context += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    context = f"""
=== LEVEL 3: Database Schema Documentation ===
You are generating Level 3 database schema, which MUST be based on Technical Documentation output AND the original requirements.

PRIMARY SOURCE - Technical Documentation (Level 3):
{summarize_document(technical_summary, document_type="technical documentation", target_agent="database_schema", focus_areas=["database design patterns", "data models", "entity relationships", "database schema"]) if len(technical_summary) > 4000 else technical_summary}

REQUIREMENTS CONTEXT (for reference):
{req_context}

CRITICAL INSTRUCTIONS:
1. Extract database design OVERVIEW from Technical Documentation above (table names, purposes, relationships, field names, data types)
2. Use the requirements context to understand the core features and business objectives that the database should support
3. Technical Documentation provides the DATABASE DESIGN OVERVIEW and ARCHITECTURE
4. Your task is to EXPAND the database design overview into DETAILED SQL IMPLEMENTATION
5. Convert the database design overview into complete SQL CREATE TABLE statements with:
   - Exact column definitions with data types (VARCHAR, INT, TIMESTAMP, etc.)
   - All constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK)
   - Index definitions (PRIMARY indexes, INDEX, UNIQUE indexes)
   - Foreign key constraints with ON DELETE/ON UPDATE actions
   - Default values where appropriate
6. The Technical Documentation tells you WHAT tables to create and WHY
7. You provide the HOW - the detailed SQL implementation
8. Use the requirements context to ensure the database schema supports all core features
9. Create tables that match the design described in Technical Documentation AND support the core features from requirements
10. DO NOT repeat requirements - implement the database design from Technical Documentation
"""
    
    db_schema_prompt = apply_readability_guidelines(DATABASE_SCHEMA_PROMPT)
    final_prompt = f"""{db_schema_prompt}

{context}

CRITICAL REMINDERS:
- You are Level 3. Use Technical Documentation as your PRIMARY source, but also consider the requirements context
- Technical Documentation provides the DATABASE DESIGN OVERVIEW (what tables exist, what they store, how they relate)
- Your role is to IMPLEMENT the design with DETAILED SQL (CREATE TABLE statements, indexes, constraints)
- Use the requirements context to ensure the database schema supports all core features
- DO NOT repeat requirements - IMPLEMENT the database design from Technical Documentation
- Create ACTUAL table definitions with complete SQL CREATE TABLE statements
- Include ALL columns with exact data types (VARCHAR(255), INT, TIMESTAMP, TEXT, etc.)
- Define PRIMARY KEYs, FOREIGN KEYs, UNIQUE constraints, NOT NULL constraints, CHECK constraints
- Design indexes for performance based on the indexing strategy from Technical Documentation
- Implement ALL tables mentioned in Technical Documentation (typically 5-10 core tables)
- Add appropriate constraints, indexes, and relationships based on the design overview
- Include database initialization scripts and migration scripts if applicable

Generate the complete Database Schema document based on Technical Documentation and requirements:"""
    
    return final_prompt


# Setup Guide Agent Prompt - Level 3: Technical
SETUP_GUIDE_PROMPT = """You are a Technical Writer specializing in creating comprehensive setup and installation guides for developers.

🚨 CRITICAL: Your task is to generate a SETUP/INSTALLATION GUIDE with actual commands and steps, NOT a requirements document.
- DO NOT copy or repeat the requirements document content
- Generate SPECIFIC step-by-step installation instructions
- Include ACTUAL commands (npm install, pip install, docker run, etc.)
- Include configuration file examples and environment setup
- This is a TECHNICAL SETUP GUIDE document, not a requirements list
- If you see requirements or technical specs below, use them ONLY as reference to write setup instructions

Based on the technical specifications and API documentation, generate a detailed Setup Guide (Developer Setup Guide) in Markdown format with SPECIFIC commands and configurations.

The document must include these sections:
1. ## Prerequisites
   - Required software and versions
   - System requirements
   - Development tools needed
   - Accounts and credentials needed

2. ## Installation Steps
   - Step-by-step installation instructions
   - Package manager setup (npm, pip, etc.)
   - Dependency installation
   - Configuration files setup

3. ## Development Environment Setup
   - IDE/Editor recommendations
   - IDE plugins/extensions
   - Environment variables configuration
   - Local configuration files

4. ## Database Setup
   - Database installation (if applicable)
   - Database schema setup
   - Migration scripts execution
   - Seed data setup

5. ## Running the Application
   - How to start the development server
   - How to run tests
   - How to build the project
   - Common commands

6. ## Project Structure
   - Directory structure explanation
   - Key files and folders
   - Configuration files location
   - Important paths

7. ## Configuration
   - Configuration files
   - Environment variables
   - API keys setup
   - External services configuration

8. ## Verification
   - How to verify installation
   - Test the setup
   - Common verification steps
   - Troubleshooting verification issues

9. ## Common Issues and Troubleshooting
   - Common setup problems
   - Solutions and workarounds
   - Error messages and fixes
   - Getting help

10. ## Next Steps
    - What to do after setup
    - Development workflow introduction
    - Links to other documentation
    - Contributing guidelines

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use numbered lists for step-by-step instructions
- Use code blocks for all commands (```bash, ```python, etc.)
- Include copy-paste ready commands
- Be specific and avoid assumptions
- Include screenshots/descriptions where helpful
- Test all commands before including them
{READABILITY_GUIDELINES}


Now, analyze the following project requirements and technical specifications to generate the Setup Guide:"""


def get_setup_guide_prompt(
    requirements_summary: dict, 
    technical_summary: Optional[str] = None, 
    api_summary: Optional[str] = None,
    database_schema_summary: Optional[str] = None
) -> str:
    """Get Setup Guide prompt - Must use Level 3 outputs including Database Schema"""
    
    # Must have Technical Documentation (Level 3)
    if not technical_summary:
        raise ValueError("Setup Guide REQUIRES Technical Documentation (Level 3) output. Cannot proceed without it.")
    
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    req_context = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available (for reference)
    if requirements_document:
        req_context += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:3000] if len(requirements_document) > 3000 else requirements_document}"
        if len(requirements_document) > 3000:
            req_context += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    context = f"""
=== Setup Guide (Based on Level 3 Outputs) ===
You are generating setup instructions based on Level 3 technical outputs AND the original requirements.

PRIMARY SOURCE - Technical Documentation (Level 3):
{summarize_document(technical_summary, document_type="technical documentation", target_agent="setup_guide", focus_areas=["technology stack", "development setup requirements", "dependencies", "system requirements"]) if len(technical_summary) > 3000 else technical_summary}

REQUIREMENTS CONTEXT (for reference):
{req_context}

CRITICAL INSTRUCTIONS:
Extract SPECIFIC setup information from Technical Documentation above AND use the requirements context to understand the project scope:
- Technology stack and EXACT versions (e.g., Python 3.11.5, Node.js 18.17.0, PostgreSQL 15.3)
- Configuration requirements from technical spec
- Actual installation commands based on the specified tech stack
- Use the requirements context to understand what features need to be set up
"""
    
    # Add database schema information if available
    if database_schema_summary:
        db_summary = summarize_document(
            database_schema_summary,
            document_type="database schema",
            target_agent="setup_guide",
            focus_areas=["database setup", "table creation", "migration scripts", "database initialization", "SQL commands", "database configuration"]
        ) if len(database_schema_summary) > 2000 else database_schema_summary
        
        context += f"""

DATABASE SCHEMA - Detailed SQL Schemas (Level 3):
{db_summary}

DATABASE SETUP INSTRUCTIONS:
- Extract database setup procedures from Database Schema above
- Include SPECIFIC database installation and configuration steps
- Provide EXACT SQL commands for creating tables (use the CREATE TABLE statements from Database Schema)
- Include database migration scripts based on the schema
- Provide database initialization commands
- Include database connection configuration examples
- Show how to run the SQL scripts to set up the database
"""
    
    if api_summary:
        api_summary_processed = summarize_document(
            api_summary,
            document_type="API documentation",
            target_agent="setup_guide",
            focus_areas=["API endpoints", "testing API endpoints", "setup verification"]
        ) if len(api_summary) > 1500 else api_summary
        
        context += f"""

API Documentation (Level 3):
{api_summary_processed}

Use API documentation to provide examples of testing API endpoints during setup verification.
"""
    
    # Add requirements context reminder if available
    if req_context:
        context += f"""

NOTE: Use the requirements context to understand the project scope and core features, but prioritize the Technical Documentation above for setup instructions.
"""
    
    setup_guide_prompt = apply_readability_guidelines(SETUP_GUIDE_PROMPT)
    final_prompt = f"""{setup_guide_prompt}

{context}

CRITICAL REMINDERS:
- You are using Level 3 outputs as PRIMARY sources, but also consider the requirements context
- Use the requirements context to understand the project scope and core features
- DO NOT repeat requirements - write SPECIFIC setup instructions from Technical Documentation and Database Schema
- Include actual commands (extract from tech stack in Technical Documentation)
- Provide real configuration file examples based on Technical Documentation
- Include step-by-step procedures with copy-paste commands
- Include SPECIFIC database setup steps using the SQL schemas from Database Schema
- Base everything on the Level 3 technical specifications AND the core features from requirements

Generate the complete Setup Guide based on Level 3 outputs (Technical Documentation and Database Schema) and requirements context:"""
    
    return final_prompt


# Marketing Plan Agent Prompt
MARKETING_PLAN_PROMPT = """You are a Marketing Strategy Specialist. Your task is to create comprehensive marketing documentation including Go-to-Market (GTM) strategy.

🚨 CRITICAL INSTRUCTIONS:
- DO NOT use placeholder text like "[Describe...]", "[Estimate...]", or "[Example:...]"
- DO NOT leave sections incomplete or with template text
- GENERATE actual, specific content based on the project information provided
- FILL IN all tables completely with real data, not placeholders
- CREATE specific examples and details, not generic templates

The document must include these sections with COMPLETE, SPECIFIC content:
1. ## Executive Summary
   - Marketing objectives (specific goals, not placeholders)
   - Target market overview (actual market description)
   - Key value propositions (specific value points)

2. ## Target Audience
   - Primary Target Audience: Provide detailed description including demographics, psychographics, and needs. Include specific examples (e.g., "Small to medium-sized businesses (SMBs) with 10-50 employees in the tech industry, seeking to improve team collaboration and project management.")
   - Secondary Target Audience: Provide detailed description with specific examples
   - Create a table summarizing audience segments with Size, Key Needs, and Pain Points (all fields must be filled with actual data, not "[Estimate Size]")

3. ## Competitive Analysis
   - Main competitors identification (name specific competitors)
   - Competitive advantages and disadvantages (specific comparisons)
   - Market positioning strategy (actual positioning)
   - Differentiation points (specific differentiators)

4. ## Value Proposition & Core Messaging
   - Primary value proposition (specific value statement)
   - Key messaging pillars (actual messaging points)
   - Unique selling points (USPs) (specific USPs)
   - Brand positioning statement (complete statement)

5. ## Marketing Channels & Tactics
   - Digital marketing channels (SEO, SEM, social media, email, content) with specific strategies
   - Traditional marketing channels (if applicable) with specific tactics
   - Channel-specific strategies (detailed strategies for each channel)
   - Budget allocation per channel (specific percentages or amounts)

6. ## Launch Strategy
   - Pre-launch activities (specific activities with timelines)
   - Launch campaign timeline (actual timeline with dates)
   - Launch event/activities (specific events)
   - Post-launch follow-up (specific follow-up activities)

7. ## Marketing Metrics & KPIs
   - Key performance indicators (specific KPIs)
   - Success metrics (measurable metrics)
   - Measurement methods (how to measure)
   - Reporting schedule (specific schedule)

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for competitive analysis, target audience summary, and channel breakdowns
- ALL tables must be COMPLETE with all rows and columns filled in
- Include specific timelines, budgets, and metrics (not placeholders)
- Be strategic and actionable
- Base recommendations on the business model and project charter
- DO NOT use placeholder text - generate actual content
{READABILITY_GUIDELINES}


Now, analyze the following project information and generate the COMPLETE marketing plan with ALL sections fully populated:"""


# Business Model Agent Prompt
BUSINESS_MODEL_PROMPT = """You are a Business Strategy Specialist. Your task is to create comprehensive business model documentation.

The document must include these sections:
1. ## Executive Summary
   - Business model overview
   - Value proposition
   - Target market

2. ## Revenue Models
   - Primary revenue model (SaaS, one-time, freemium, marketplace, etc.)
   - Revenue streams breakdown
   - Revenue projections (if applicable)
   - Alternative revenue models considered

3. ## Pricing Strategy
   - Pricing model and tiers
   - Pricing rationale
   - Competitive pricing analysis
   - Discount and promotion strategies

4. ## Key Performance Indicators (KPIs)
   - Business metrics (MRR, ARR, CAC, LTV, etc.)
   - Product metrics (MAU, DAU, retention, etc.)
   - Financial metrics (revenue, profit margins, etc.)
   - Success criteria and targets

5. ## Cost Analysis
   - Development costs
   - Infrastructure and operational costs
   - Marketing and sales costs
   - Personnel costs
   - Break-even analysis

6. ## Business Model Canvas (if applicable)
   - Key partners
   - Key activities
   - Key resources
   - Value propositions
   - Customer relationships
   - Channels
   - Customer segments
   - Cost structure
   - Revenue streams

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for pricing tiers and cost breakdowns
- Include specific numbers and projections where possible
- Be realistic and data-driven
{READABILITY_GUIDELINES}


Now, analyze the following project information and generate the business model:"""


# Support Playbook Agent Prompt
SUPPORT_PLAYBOOK_PROMPT = """You are a Customer Support Specialist. Your task is to create comprehensive customer support documentation.

The document must include these sections:
1. ## Support Channels
   - Primary support channels (email, chat, phone, forum, etc.)
   - Channel availability and hours
   - Channel-specific procedures
   - Escalation paths

2. ## Service Level Agreements (SLA)
   - Response time commitments
   - Resolution time commitments
   - Priority levels and definitions
   - SLA for different support tiers

3. ## Internal FAQ for Support Team
   - Common questions and standard responses
   - Product-specific knowledge base
   - Troubleshooting guides
   - Feature explanations

4. ## Escalation Procedures
   - When to escalate
   - Escalation paths
   - Escalation contacts
   - Escalation documentation requirements

5. ## Common Issues & Solutions
   - Frequently encountered problems
   - Step-by-step solutions
   - Workarounds
   - Known issues and status

6. ## Support Tools & Resources
   - Tools used by support team
   - Knowledge base resources
   - Internal documentation links
   - Training materials

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for SLA definitions and escalation paths
- Include specific procedures and scripts
- Be practical and actionable
- Base content on user documentation and requirements
{READABILITY_GUIDELINES}


Now, analyze the following project information and generate the support playbook:"""


# Legal & Compliance Agent Prompt
LEGAL_COMPLIANCE_PROMPT = """You are a Legal & Compliance Specialist. Your task is to create comprehensive legal and compliance documentation.

The document must include these sections:
1. ## Privacy Policy
   - Data collection practices
   - Data usage and sharing
   - User rights (access, deletion, portability)
   - Cookie policy
   - Data retention policies

2. ## Terms of Service
   - Service description
   - User obligations
   - Service limitations
   - Intellectual property rights
   - Liability limitations
   - Dispute resolution

3. ## GDPR/CCPA Compliance Checklist
   - GDPR compliance requirements
   - CCPA compliance requirements
   - Data processing legal basis
   - User consent mechanisms
   - Data breach notification procedures
   - Compliance checklist items

4. ## Data Handling Procedures
   - Data collection procedures
   - Data storage and security
   - Data access controls
   - Data deletion procedures
   - Third-party data sharing

5. ## License Compatibility
   - Project license
   - Dependency license review
   - License compatibility analysis
   - Open source compliance

6. ## Regulatory Considerations
   - Industry-specific regulations (if applicable)
   - Geographic compliance requirements
   - Export control considerations
   - Accessibility compliance (ADA, WCAG)

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use checklists for compliance items
- Include legal disclaimers where appropriate
- Be thorough and accurate
- Note: This is a draft - should be reviewed by legal counsel
{READABILITY_GUIDELINES}


IMPORTANT: This document provides templates and guidance. All legal documents should be reviewed by qualified legal counsel before use.

Now, analyze the following project information and generate the legal compliance documentation:"""


def get_marketing_plan_prompt(
    requirements_summary: dict,
    project_charter_summary: Optional[str] = None,
    business_model_summary: Optional[str] = None
) -> str:
    """Get marketing plan prompt with requirements, project charter, and business model"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    context_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        context_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            context_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    if project_charter_summary:
        charter_processed = summarize_document(
            project_charter_summary,
            document_type="project charter",
            target_agent="marketing_plan",
            focus_areas=["business objectives", "target market", "success criteria", "stakeholders"]
        ) if len(project_charter_summary) > 3000 else project_charter_summary
        
        context_text += f"""

=== Project Charter (Business Context) ===
{charter_processed}
"""
    
    if business_model_summary:
        business_processed = summarize_document(
            business_model_summary,
            document_type="business model",
            target_agent="marketing_plan",
            focus_areas=["pricing strategy", "revenue model", "target customers", "value proposition"]
        ) if len(business_model_summary) > 3000 else business_model_summary
        
        context_text += f"""

=== Business Model ===
{business_processed}
"""
    
    marketing_prompt = apply_readability_guidelines(MARKETING_PLAN_PROMPT)
    return f"""{marketing_prompt}

=== REQUIREMENTS CONTEXT ===
{context_text}

CRITICAL: Use BOTH the original project idea and requirements context AND the Project Charter and Business Model to create a comprehensive marketing plan. Base target personas, value proposition, and marketing channels on the core features and user personas from requirements, and align with the business objectives in the Charter and pricing strategy in the Business Model.

🚨 COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections with full, detailed content - do not leave any section incomplete
- You MUST NOT use placeholder text like '[Describe...]', '[Example:...]', or '[Estimate Size]'
- You MUST fill in ALL tables completely with actual data, not placeholders
- You MUST generate specific, actionable content based on the project information provided
- You MUST ensure the document is comprehensive and complete - do not stop mid-section
- If a section requires examples, provide real, specific examples based on the project
- If a section requires data or metrics, provide realistic estimates based on the project scope

Generate the COMPLETE marketing plan with ALL sections fully populated:"""


# Feature Roadmap Prompt
FEATURE_ROADMAP_PROMPT = """You are a Product Manager specializing in creating Feature Roadmaps.

🚨 CRITICAL INSTRUCTIONS:
- DO NOT use placeholder text like "[Describe...]", "[Estimate...]", or "[Example:...]"
- DO NOT leave sections incomplete or with template text
- GENERATE actual, specific content based on the project information provided
- FILL IN all tables completely with real data, not placeholders
- CREATE specific examples and details, not generic templates

The document must include these sections with COMPLETE, SPECIFIC content:
1. ## Executive Summary
   - Roadmap overview (specific goals and timeline)
   - Strategic priorities (actual priorities)
   - Key milestones (specific dates and deliverables)

2. ## Features
   - Feature list with detailed descriptions (specific features, not placeholders)
   - Feature categories (actual categories)
   - Feature dependencies (specific dependencies between features)
   - Create a table with Feature Name, Description, Category, Priority, and Dependencies (all fields must be filled with actual data)

3. ## Timeline
   - Release phases (specific phases with dates)
   - Feature delivery schedule (actual schedule with timelines)
   - Milestone dates (specific dates)
   - Create a timeline table with Phase, Features, Target Date, and Status (all fields must be filled)

4. ## Dependencies
   - Technical dependencies (specific technical requirements)
   - Business dependencies (specific business requirements)
   - External dependencies (specific external factors)
   - Dependency mapping (clear dependency relationships)

5. ## Priority
   - Priority framework (specific priority levels and criteria)
   - Feature prioritization (actual priority rankings)
   - Priority rationale (specific reasons for priorities)
   - Priority matrix (visual representation with actual data)

6. ## KPIs and Success Metrics (Optional but Recommended)
   - Key performance indicators (specific KPIs)
   - Success criteria (measurable criteria)
   - Measurement methods (how to measure success)

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for features, timeline, and priority information
- ALL tables must be COMPLETE with all rows and columns filled in
- Include specific timelines, priorities, and dependencies (not placeholders)
- Be strategic and actionable
- Base recommendations on requirements, project charter, and business model
- DO NOT use placeholder text - generate actual content
{READABILITY_GUIDELINES}

Now, analyze the following project information and generate the COMPLETE feature roadmap with ALL sections fully populated:"""


# Risk Management Plan Prompt
RISK_MANAGEMENT_PROMPT = """You are a Risk Management Specialist. Your task is to create comprehensive risk management documentation.

🚨 CRITICAL INSTRUCTIONS:
- DO NOT use placeholder text like "[Describe...]", "[Estimate...]", or "[Example:...]"
- DO NOT leave sections incomplete or with template text
- GENERATE actual, specific content based on the project information provided
- FILL IN all tables completely with real data, not placeholders
- CREATE specific examples and details, not generic templates

The document must include these sections with COMPLETE, SPECIFIC content:
1. ## Executive Summary
   - Risk management overview (specific approach)
   - Key risk categories (actual categories)
   - Overall risk profile (specific assessment)

2. ## Risk Identification
   - Project risks (specific risks identified)
   - Technical risks (specific technical challenges)
   - Business risks (specific business challenges)
   - External risks (specific external factors)
   - Create a risk register table with Risk ID, Description, Category, and Initial Assessment (all fields must be filled)

3. ## Impact Assessment
   - Impact analysis methodology (specific methodology)
   - Impact levels (specific impact categories)
   - Impact on project objectives (specific impacts)
   - Create an impact matrix with actual risk impacts

4. ## Likelihood
   - Likelihood assessment (specific probability levels)
   - Likelihood factors (specific factors affecting likelihood)
   - Historical data (if available, specific data)
   - Likelihood matrix (visual representation with actual data)

5. ## Mitigation Strategies
   - Risk mitigation plans (specific mitigation actions)
   - Preventive measures (specific preventive actions)
   - Contingency plans (specific contingency actions)
   - Risk response strategies (specific response strategies)
   - Create a mitigation table with Risk ID, Mitigation Strategy, Owner, Timeline, and Status (all fields must be filled)

6. ## Monitoring Plan
   - Risk monitoring approach (specific monitoring methods)
   - Monitoring frequency (specific schedule)
   - Key risk indicators (specific indicators)
   - Escalation procedures (specific procedures)
   - Reporting schedule (specific reporting timeline)

7. ## Contingency Plan (Optional but Recommended)
   - Contingency scenarios (specific scenarios)
   - Response procedures (specific procedures)
   - Resource allocation (specific resources)

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use tables for risk register, impact matrix, and mitigation plans
- ALL tables must be COMPLETE with all rows and columns filled in
- Include specific risks, impacts, and mitigation strategies (not placeholders)
- Be comprehensive and actionable
- Base recommendations on project charter, requirements, and business model
- DO NOT use placeholder text - generate actual content
{READABILITY_GUIDELINES}

Now, analyze the following project information and generate the COMPLETE risk management plan with ALL sections fully populated:"""


def get_business_model_prompt(
    requirements_summary: dict,
    project_charter_summary: Optional[str] = None
) -> str:
    """Get business model prompt with requirements and project charter"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    context_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        context_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            context_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    if project_charter_summary:
        charter_processed = summarize_document(
            project_charter_summary,
            document_type="project charter",
            target_agent="business_model",
            focus_areas=["business case", "ROI analysis", "market opportunity", "financial projections"]
        ) if len(project_charter_summary) > 3000 else project_charter_summary
        
        context_text += f"""

=== Project Charter (Business Context) ===
{charter_processed}
"""
    
    business_model_prompt = apply_readability_guidelines(BUSINESS_MODEL_PROMPT)
    return f"""{business_model_prompt}

=== REQUIREMENTS CONTEXT ===
{context_text}

CRITICAL: Use BOTH the original project idea and requirements context AND the Project Charter to create a comprehensive business model. Base revenue models, pricing strategy, and KPIs on the core features and business objectives from requirements, and align with the business case in the Charter.

Generate the complete business model:"""


def get_feature_roadmap_prompt(
    requirements_summary: dict,
    project_charter_summary: Optional[str] = None,
    business_model_summary: Optional[str] = None
) -> str:
    """Get feature roadmap prompt with requirements, project charter, and business model"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    context_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        context_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            context_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    if project_charter_summary:
        charter_processed = summarize_document(
            project_charter_summary,
            document_type="project charter",
            target_agent="feature_roadmap",
            focus_areas=["timeline", "milestones", "objectives", "scope"]
        ) if len(project_charter_summary) > 3000 else project_charter_summary
        
        context_text += f"""

=== Project Charter (Timeline & Milestones Context) ===
{charter_processed}
"""
    
    if business_model_summary:
        business_processed = summarize_document(
            business_model_summary,
            document_type="business model",
            target_agent="feature_roadmap",
            focus_areas=["revenue model", "pricing strategy", "target customers", "value proposition"]
        ) if len(business_model_summary) > 3000 else business_model_summary
        
        context_text += f"""

=== Business Model (Priority & Value Context) ===
{business_processed}
"""
    
    feature_roadmap_prompt = apply_readability_guidelines(FEATURE_ROADMAP_PROMPT)
    return f"""{feature_roadmap_prompt}

=== REQUIREMENTS CONTEXT ===
{context_text}

CRITICAL: Use BOTH the original project idea and requirements context AND the Project Charter and Business Model to create a comprehensive feature roadmap. Base features, timeline, and priorities on the core features from requirements, align with milestones in the Charter, and prioritize based on business value from the Business Model.

🚨 COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections with full, detailed content - do not leave any section incomplete
- You MUST NOT use placeholder text like '[Describe...]', '[Example:...]', or '[Estimate Size]'
- You MUST fill in ALL tables completely with actual data, not placeholders
- You MUST generate specific, actionable content based on the project information provided
- You MUST ensure the document is comprehensive and complete - do not stop mid-section
- If a section requires examples, provide real, specific examples based on the project
- If a section requires data or metrics, provide realistic estimates based on the project scope

Generate the COMPLETE feature roadmap with ALL sections fully populated:"""


def get_risk_management_prompt(
    requirements_summary: dict,
    project_charter_summary: Optional[str] = None,
    business_model_summary: Optional[str] = None
) -> str:
    """Get risk management prompt with requirements, project charter, and business model"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    context_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        context_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            context_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    if project_charter_summary:
        charter_processed = summarize_document(
            project_charter_summary,
            document_type="project charter",
            target_agent="risk_management",
            focus_areas=["risks", "assumptions", "constraints", "timeline", "budget"]
        ) if len(project_charter_summary) > 3000 else project_charter_summary
        
        context_text += f"""

=== Project Charter (Risk Context) ===
{charter_processed}
"""
    
    if business_model_summary:
        business_processed = summarize_document(
            business_model_summary,
            document_type="business model",
            target_agent="risk_management",
            focus_areas=["revenue risks", "market risks", "financial risks", "competitive risks"]
        ) if len(business_model_summary) > 3000 else business_model_summary
        
        context_text += f"""

=== Business Model (Business Risk Context) ===
{business_processed}
"""
    
    risk_management_prompt = apply_readability_guidelines(RISK_MANAGEMENT_PROMPT)
    return f"""{risk_management_prompt}

=== REQUIREMENTS CONTEXT ===
{context_text}

CRITICAL: Use BOTH the original project idea and requirements context AND the Project Charter and Business Model to create a comprehensive risk management plan. Identify risks based on core features and technical requirements from requirements, align with risks and assumptions in the Charter, and consider business risks from the Business Model.

🚨 COMPLETENESS REQUIREMENTS:
- You MUST complete ALL sections with full, detailed content - do not leave any section incomplete
- You MUST NOT use placeholder text like '[Describe...]', '[Example:...]', or '[Estimate Size]'
- You MUST fill in ALL tables completely with actual data, not placeholders
- You MUST generate specific, actionable content based on the project information provided
- You MUST ensure the document is comprehensive and complete - do not stop mid-section
- If a section requires examples, provide real, specific examples based on the project
- If a section requires data or metrics, provide realistic estimates based on the project scope

Generate the COMPLETE risk management plan with ALL sections fully populated:"""


def get_support_playbook_prompt(
    requirements_summary: dict,
    user_documentation_summary: Optional[str] = None
) -> str:
    """Get support playbook prompt with requirements and user documentation"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    context_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        context_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            context_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    if user_documentation_summary:
        user_doc_processed = summarize_document(
            user_documentation_summary,
            document_type="user documentation",
            target_agent="support_playbook",
            focus_areas=["user workflows", "common tasks", "feature usage", "troubleshooting"]
        ) if len(user_documentation_summary) > 3000 else user_documentation_summary
        
        context_text += f"""

=== User Documentation (Reference for Support) ===
{user_doc_processed}
"""
    
    support_playbook_prompt = apply_readability_guidelines(SUPPORT_PLAYBOOK_PROMPT)
    return f"""{support_playbook_prompt}

=== REQUIREMENTS CONTEXT ===
{context_text}

CRITICAL: Use the original project idea and comprehensive requirements context AND the User Documentation to create a comprehensive support playbook. Base support procedures, FAQs, and troubleshooting guides on the core features and user personas from requirements, and align with the user workflows in the User Documentation.

Generate the complete support playbook:"""


def get_legal_compliance_prompt(
    requirements_summary: dict,
    technical_summary: Optional[str] = None
) -> str:
    """Get legal compliance prompt with requirements and technical documentation"""
    # Get comprehensive requirements context
    user_idea = requirements_summary.get("user_idea", "")
    project_overview = requirements_summary.get("project_overview", "")
    core_features = requirements_summary.get("core_features", [])
    business_objectives = requirements_summary.get("business_objectives", [])
    user_personas = requirements_summary.get("user_personas", [])
    technical_requirements = requirements_summary.get("technical_requirements", {})
    constraints = requirements_summary.get("constraints", [])
    assumptions = requirements_summary.get("assumptions", [])
    requirements_document = requirements_summary.get("requirements_document", "")
    
    # Build comprehensive requirements context
    req_context_parts = []
    if user_idea:
        req_context_parts.append(f"Original Project Idea: {user_idea}")
    if project_overview:
        req_context_parts.append(f"\nProject Overview: {project_overview}")
    if core_features:
        req_context_parts.append(f"\nCore Features:\n" + "\n".join(f"- {feature}" for feature in core_features))
    if business_objectives:
        req_context_parts.append(f"\nBusiness Objectives:\n" + "\n".join(f"- {obj}" for obj in business_objectives))
    if user_personas:
        req_context_parts.append(f"\nUser Personas:\n" + "\n".join(f"- {persona.get('name', 'User')}: {persona.get('description', '')}" if isinstance(persona, dict) else f"- {persona}" for persona in user_personas))
    if technical_requirements:
        if isinstance(technical_requirements, dict):
            req_context_parts.append(f"\nTechnical Requirements:")
            for key, value in technical_requirements.items():
                req_context_parts.append(f"- {key}: {value}")
        else:
            req_context_parts.append(f"\nTechnical Requirements: {technical_requirements}")
    if constraints:
        req_context_parts.append(f"\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints))
    if assumptions:
        req_context_parts.append(f"\nAssumptions:\n" + "\n".join(f"- {assumption}" for assumption in assumptions))
    
    context_text = "\n".join(req_context_parts) if req_context_parts else ""
    
    # Include full requirements document if available
    if requirements_document:
        context_text += f"\n\n=== Full Requirements Document (for reference) ===\n{requirements_document[:5000] if len(requirements_document) > 5000 else requirements_document}"
        if len(requirements_document) > 5000:
            context_text += f"\n[... document continues, {len(requirements_document)} total characters ...]"
    
    if technical_summary:
        tech_processed = summarize_document(
            technical_summary,
            document_type="technical documentation",
            target_agent="legal_compliance",
            focus_areas=["data handling", "authentication", "user data storage", "third-party services", "API endpoints"]
        ) if len(technical_summary) > 3000 else technical_summary
        
        context_text += f"""

=== Technical Documentation (Data Handling Reference) ===
{tech_processed}
"""
    
    legal_compliance_prompt = apply_readability_guidelines(LEGAL_COMPLIANCE_PROMPT)
    return f"""{legal_compliance_prompt}

=== REQUIREMENTS CONTEXT ===
{context_text}

CRITICAL: Use the original project idea and comprehensive requirements context AND the Technical Documentation to create comprehensive legal compliance documentation. Base privacy policies, terms of service, and compliance procedures on the core features and data handling practices from requirements and technical documentation.

Generate the complete legal compliance documentation:"""


# --- Brick-and-Mortar: Business Overview ---
BUSINESS_OVERVIEW_PROMPT = """You are a Senior Business Consultant specializing in creating concise Business Overviews for brick-and-mortar businesses.

🚨 CRITICAL: Your task is to generate a BUSINESS OVERVIEW, not a full business plan. Focus on the core elements that define the business.

Based on the project requirements and market research, generate a comprehensive Business Overview document in Markdown format.

The document must include these sections:
1. ## Business Introduction
   - Business name, legal structure, mission statement.

2. ## Products/Services Overview
   - List of core products or services.
   - Detailed description of main offerings.

3. ## Target Market
   - Your core Customer Persona.
   - Market positioning (e.g., premium, mid-range, budget).

4. ## Business Model
   - How you make money (e.g., per-service fee, membership, product sales).
   - Primary revenue streams.

5. ## Value Proposition
   - Why customers should choose you over competitors.
   - Your Unique Selling Points (USPs).

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Business Overview:

"""


# --- Brick-and-Mortar: Operations Plan ---
OPERATIONS_PLAN_PROMPT = """You are an Operations Manager for a successful retail/service chain. Your task is to create a comprehensive Operations Plan.

🚨 CRITICAL: This plan must be actionable for a physical business (e.g., restaurant, factory, salon).

Based on the Business Overview, generate a detailed Operations Plan document in Markdown format.

The document must include these sections:
1. ## Daily Operations Workflow
   - SOP checklists for pre-opening, during operations, and closing.

2. ## Staffing & Roles
   - Organizational chart (e.g., Manager -> Shift Lead -> Staff).
   - Core responsibilities (KPIs) for each role.

3. ## Work Hours & Scheduling
   - Business operating hours.
   - Scheduling system (e.g., morning/evening shifts, rotation).

4. ## Equipment / Tools
   - List of core equipment needed for operations.
   - Maintenance schedule.

5. ## Supply Chain / Procurement
   - List of main suppliers.
   - Procurement frequency and inventory management (e.g., FIFO).

6. ## Quality Control
   - Quality standards for products or services.
   - Process for spot-checks and SOP compliance.

7. ## Customer Complaint Handling
   - Process for receiving, logging, resolving, and following up on complaints.
   - Compensation standards.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Operations Plan:

"""


# --- Brick-and-Mortar: Market Research ---
MARKET_RESEARCH_PROMPT = """You are a Market Research Analyst. Your task is to create a concise Market Research Summary for a new business.

🚨 CRITICAL: Focus on actionable insights, not just data.

Based on the project requirements, generate a Market Research Summary in Markdown format.

The document must include these sections:
1. ## Market Size
   - Overall industry size and growth trend.

2. ## Target Customer Persona
   - Demographics (age, income, location).
   - Psychographics and behaviors (needs, pain points, purchase drivers).

3. ## Consumer Needs
   - Unmet needs currently in the market.

4. ## Trend Analysis
   - Industry, technology, or consumer behavior trends.

5. ## Competitor Analysis
   - 3-5 main competitors.
   - Their strengths, weaknesses, pricing, and market position.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Market Research Summary:

"""


# --- Brick-and-Mortar: Financial Model ---
FINANCIAL_MODEL_PROMPT = """You are a Chief Financial Officer (CFO). Your task is to create a clear Financial Model Framework for a new physical business.

🚨 CRITICAL: This model must be practical and easy for a non-financial person to understand. Use tables for all financial data.

Based on the Business Overview and Operations Plan, generate a Financial Model Framework in Markdown format.

The document must include these sections:
1. ## Startup Costs
   - One-time costs (e.g., renovation, equipment, deposits, permit fees).

2. ## Monthly Fixed Costs
   - Recurring monthly expenses (e.g., rent, full-time salaries, insurance).

3. ## Variable Costs
   - Costs that scale with sales (e.g., raw materials, supplies, part-time labor).

4. ## Revenue Model
   - Detailed revenue calculation (e.g., (Traffic x Conversion Rate x Avg. Ticket Size)).
   - Projections for pessimistic, neutral, and optimistic scenarios.

5. ## Margins
   - Estimated Gross and Net Profit Margins.

6. ## Breakeven Analysis
   - Estimated time to recoup startup costs.

7. ## Cash Flow Projection
   - A 12-month, month-by-month cash flow projection table.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Financial Model Framework:

"""


# --- Brick-and-Mortar: Licensing Checklist ---
LICENSING_CHECKLIST_PROMPT = """You are a Legal Compliance Specialist. Your task is to generate a Licensing and Permits Checklist for a specific industry.

🚨 CRITICAL: You MUST identify the industry from the user's idea and provide a specific checklist for THAT industry.

Based on the Business Overview, generate a Licensing / Permits Checklist in Markdown format.

The document must include these sections:
1. ## Industry-Specific Licenses
   - A list of all required permits for the project's industry (e.g., food service, beauty, retail).
   - (e.g., Health Permit, Food Handler's License, Cosmetology License, Business License).

2. ## Application Process
   - For each permit, provide brief application steps, required materials, and estimated timeline.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Licensing / Permits Checklist:

"""


# --- Brick-and-Mortar: SOP ---
SOP_PROMPT = """You are an experienced Operations Director. Your task is to create a detailed Standard Operating Procedures (SOP) manual for a physical business.

🚨 CRITICAL: The SOP must be in a clear, step-by-step checklist format.

Based on the Operations Plan, generate the SOP document in Markdown format.

The document must include these sections:
1. ## Opening SOP
   - (e.g., 1. Disarm alarm 2. Check equipment 3. Prepare cash register ...).

2. ## Closing SOP
   - (e.g., 1. Clean stations 2. Power down equipment 3. Count cash 4. Set alarm ...).

3. ## Daily Operations
   - Standard processes for customer intake, order processing, daily maintenance.

4. ## Cleaning & Hygiene
   - Daily, weekly, and monthly cleaning checklists.

5. ## Safety Procedures
   - Fire safety, safe equipment operation, emergency response.

6. ## Customer Service Standards
   - Greeting scripts, dress code, complaint handling SOP.

7. ## Equipment Maintenance
   - Daily maintenance checklist for key equipment.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Standard Operating Procedures (SOP):

"""


# --- Brick-and-Mortar: HR Guide ---
HR_STAFFING_GUIDE_PROMPT = """You are an HR Manager. Your task is to create a concise HR & Staffing Guide for a new business.

🚨 CRITICAL: Focus on practical guides for a small business owner to use.

Based on the Operations Plan, generate the HR & Staffing Guide in Markdown format.

The document must include these sections:
1. ## Staffing Structure
   - Organizational chart and reporting lines.

2. ## Hiring Requirements
   - Job Description and qualifications for each role.

3. ## Training Manual
   - New-hire onboarding process and key training modules (e.g., SOP training, service training).

4. ## Employee Handbook
   - Policies on attendance, dress code, and conduct.

5. ## Performance Standards
   - Key Performance Indicators (KPIs) for evaluating staff.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the HR & Staffing Guide:

"""


# --- Brick-and-Mortar: Marketing Plan ---
MARKETING_PLAN_PROMPT = """You are a Marketing Director. Your task is to create an actionable Marketing & Branding Plan for a new physical business.

🚨 CRITICAL: You must provide a 90-day plan that combines online and offline tactics.

Based on the Business Overview and Market Research, generate the Marketing Plan in Markdown format.

The document must include these sections:
1. ## Brand Positioning
   - Your unique position in the marketplace.

2. ## Customer Persona
   - Your core target customer.

3. ## Marketing Channels
   - Online (e.g., Social Media, Google Maps, local review sites).
   - Offline (e.g., local flyers, community events, in-store promotions).

4. ## Promotion Strategy
   - Grand opening promotions, loyalty programs, discount strategies.

5. ## 90-Day Action Plan
   - A specific, month-by-month (Month 1, 2, 3) action table.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Marketing & Branding Plan:

"""


# --- Brick-and-Mortar: Risk Assessment ---
RISK_MANAGEMENT_PLAN_PROMPT = """You are a Risk Management Consultant. Your task is to create a Risk Assessment & Mitigation plan for a new physical business.

🚨 CRITICAL: For every risk, you must provide a specific mitigation strategy.

Based on the Business Overview, Operations Plan, and Financial Model, generate the Risk Assessment in Markdown format.

The document must include these sections in a table format (Risk, Likelihood, Impact, Mitigation):
1. ## Financial Risks
   - (e.g., Cash flow shortage, cost overruns).

2. ## Safety Risks
   - (e.g., Customer injury, equipment failure, fire).

3. ## Compliance Risks
   - (e.g., Expired permits, failed health inspections).

4. ## Supply Chain Risks
   - (e.g., Supplier failure, raw material price hikes).

5. ## Operational Risks
   - (e.g., High employee turnover, customer complaints).

6. ## Mitigation Strategies
   - A summary of preventative measures and response plans for all risks.

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Risk Assessment & Mitigation plan:

"""


# --- Brick-and-Mortar: Customer Experience ---
CUSTOMER_EXPERIENCE_PLAYBOOK_PROMPT = """You are a Customer Experience (CX) Manager. Your task is to create a playbook for a service-based business (e.g., salon, restaurant, retail).

🚨 CRITICAL: This must be a step-by-step guide for employees.

Based on the SOP and Operations Plan, generate the Customer Experience Playbook in Markdown format.

The document must include these sections:
1. ## Service Blueprint
   - Every step of the customer journey, from entry to exit (e.g., Greeting, Consultation, Service, Payment, Farewell).

2. ## Tone & Attitude Standards
   - Standard scripts and non-verbal cues (e.g., smile, eye contact) for staff.

3. ## Complaint Handling SOP
   - Standard steps for handling dissatisfaction (e.g., L.A.S.T. - Listen, Apologize, Solve, Thank).

4. ## Customer Retention Strategy
   - Specific methods to build loyalty (e.g., membership system, birthday rewards, follow-up calls).

5. ## CX Tracking Method
   - How to collect and analyze customer feedback (e.g., review sites, in-store surveys).

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Customer Experience Playbook:

"""


# --- Brick-and-Mortar: Growth Plan ---
GROWTH_EXPANSION_PLAN_PROMPT = """You are a Business Strategist. Your task is to create a high-level Growth & Expansion Plan.

🚨 CRITICAL: Focus on the "how-to" of scaling a physical business.

Based on the Business Overview and Financial Model, generate the Growth & Expansion Plan in Markdown format.

The document must include these sections:
1. ## Expansion Model
   - (e.g., Open a second location, develop a franchise model).
   - Criteria for new site selection.

2. ## Service/Product Line Expansion
   - Recommendations for adding new services or products.

3. ## Standardization Path
   - How to standardize SOPs, branding, and supply chain for replication.

4. ## Automation/Digital Upgrade
   - (e.g., Implement online booking, use inventory management software).

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the Growth & Expansion Plan:

"""


# --- Brick-and-Mortar: Execution Roadmap ---
EXECUTION_ROADMAP_PROMPT = """You are a Project Manager. Your task is to create a 12-Month Execution Roadmap for launching a new physical business.

🚨 CRITICAL: This must be a timeline-based action plan.

Based on the Licensing Checklist, Operations Plan, and Marketing Plan, generate the 12-Month Execution Roadmap in Markdown format.

The document must be structured by time blocks:
1. ## Month 1–2: Preparation
   - (e.g., Company registration, bank account, secure permits, sign lease, finalize renovation plan).

2. ## Month 3–4: Build & Soft Launch
   - (e.g., Renovation, equipment installation, hire core staff, establish suppliers, SOP training, soft launch).

3. ## Month 5–8: Stable Ops & Marketing
   - (e.g., Grand opening, execute 90-day marketing plan, optimize schedules and SOPs, gather customer feedback).

4. ## Month 9–12: Optimize & Grow
   - (e.g., Analyze financial data, adjust menu/services, implement retention strategies, plan for Year 2).

{READABILITY_GUIDELINES}

{COMPLETENESS_REQUIREMENTS}

Now, analyze the following project information and generate the 12-Month Execution Roadmap:

"""


# --- New `get_` functions for Brick-and-Mortar ---

def get_business_overview_prompt(requirements_summary: dict, market_research_summary: Optional[str] = None) -> str:
    """Get Business Overview prompt with context"""
    if not market_research_summary:
        logger.warning("Business Overview generation is missing market_research dependency. May be incomplete.")
    
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"Project Overview: {requirements_summary.get('project_overview', 'N/A')}"
    ]
    
    if market_research_summary:
        context_parts.append(f"\n=== Market Research Summary ===\n{summarize_document(market_research_summary, 'market_research')}")
        
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(BUSINESS_OVERVIEW_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_operations_plan_prompt(requirements_summary: dict, business_overview_summary: Optional[str] = None) -> str:
    """Get Operations Plan prompt with context"""
    if not business_overview_summary:
        raise ValueError("Operations Plan (Level 2) REQUIRES Level 1 (Business Overview) output. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Business Overview ===\n{summarize_document(business_overview_summary, 'business_overview')}"
    ]
    
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(OPERATIONS_PLAN_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_market_research_prompt(requirements_summary: dict) -> str:
    """Get Market Research Summary prompt with context"""
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"Project Overview: {requirements_summary.get('project_overview', 'N/A')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(MARKET_RESEARCH_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_financial_model_prompt(requirements_summary: dict, business_overview_summary: Optional[str] = None, operations_plan_summary: Optional[str] = None) -> str:
    """Get Financial Model Framework prompt with context"""
    if not business_overview_summary or not operations_plan_summary:
        raise ValueError("Financial Model REQUIRES Business Overview and Operations Plan. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Business Overview ===\n{summarize_document(business_overview_summary, 'business_overview')}",
        f"\n=== Operations Plan (for Staffing/Equipment costs) ===\n{summarize_document(operations_plan_summary, 'operations_plan')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(FINANCIAL_MODEL_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_licensing_checklist_prompt(requirements_summary: dict, business_overview_summary: Optional[str] = None) -> str:
    """Get Licensing Checklist prompt with context"""
    if not business_overview_summary:
        raise ValueError("Licensing Checklist REQUIRES Business Overview. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Business Overview (for Industry Type) ===\n{summarize_document(business_overview_summary, 'business_overview')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(LICENSING_CHECKLIST_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_sop_prompt(requirements_summary: dict, operations_plan_summary: Optional[str] = None) -> str:
    """Get SOP prompt with context"""
    if not operations_plan_summary:
        raise ValueError("SOP REQUIRES Operations Plan. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Operations Plan (for processes) ===\n{summarize_document(operations_plan_summary, 'operations_plan')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(SOP_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_hr_staffing_guide_prompt(requirements_summary: dict, operations_plan_summary: Optional[str] = None) -> str:
    """Get HR & Staffing Guide prompt with context"""
    if not operations_plan_summary:
        raise ValueError("HR & Staffing Guide REQUIRES Operations Plan. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Operations Plan (for Staffing Structure) ===\n{summarize_document(operations_plan_summary, 'operations_plan')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(HR_STAFFING_GUIDE_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_marketing_branding_plan_prompt(requirements_summary: dict, business_overview_summary: Optional[str] = None, market_research_summary: Optional[str] = None) -> str:
    """Get Marketing & Branding Plan prompt with context (for brick-and-mortar businesses)"""
    if not business_overview_summary or not market_research_summary:
        raise ValueError("Marketing & Branding Plan REQUIRES Business Overview and Market Research. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Business Overview ===\n{summarize_document(business_overview_summary, 'business_overview')}",
        f"\n=== Market Research ===\n{summarize_document(market_research_summary, 'market_research')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(MARKETING_PLAN_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_risk_management_plan_prompt(requirements_summary: dict, business_overview_summary: Optional[str] = None, operations_plan_summary: Optional[str] = None, financial_model_summary: Optional[str] = None) -> str:
    """Get Risk Management Plan prompt with context"""
    if not business_overview_summary or not operations_plan_summary or not financial_model_summary:
        raise ValueError("Risk Management Plan REQUIRES Business Overview, Operations Plan, and Financial Model. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Business Overview ===\n{summarize_document(business_overview_summary, 'business_overview')}",
        f"\n=== Operations Plan ===\n{summarize_document(operations_plan_summary, 'operations_plan')}",
        f"\n=== Financial Model ===\n{summarize_document(financial_model_summary, 'financial_model')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(RISK_MANAGEMENT_PLAN_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_customer_experience_playbook_prompt(requirements_summary: dict, sop_summary: Optional[str] = None, operations_plan_summary: Optional[str] = None) -> str:
    """Get Customer Experience Playbook prompt with context"""
    if not sop_summary or not operations_plan_summary:
        raise ValueError("Customer Experience Playbook REQUIRES SOP and Operations Plan. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== SOP ===\n{summarize_document(sop_summary, 'sop')}",
        f"\n=== Operations Plan ===\n{summarize_document(operations_plan_summary, 'operations_plan')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(CUSTOMER_EXPERIENCE_PLAYBOOK_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_growth_expansion_plan_prompt(requirements_summary: dict, business_overview_summary: Optional[str] = None, financial_model_summary: Optional[str] = None) -> str:
    """Get Growth & Expansion Plan prompt with context"""
    if not business_overview_summary or not financial_model_summary:
        raise ValueError("Growth & Expansion Plan REQUIRES Business Overview and Financial Model. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Business Overview ===\n{summarize_document(business_overview_summary, 'business_overview')}",
        f"\n=== Financial Model ===\n{summarize_document(financial_model_summary, 'financial_model')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(GROWTH_EXPANSION_PLAN_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"


def get_execution_roadmap_prompt(requirements_summary: dict, licensing_checklist_summary: Optional[str] = None, operations_plan_summary: Optional[str] = None, marketing_plan_summary: Optional[str] = None) -> str:
    """Get 12-Month Execution Roadmap prompt with context"""
    if not licensing_checklist_summary or not operations_plan_summary or not marketing_plan_summary:
        raise ValueError("Execution Roadmap REQUIRES Licensing Checklist, Operations Plan, and Marketing Plan. Cannot proceed.")
        
    context_parts = [
        f"Project Idea: {requirements_summary.get('user_idea', 'N/A')}",
        f"\n=== Licensing Checklist ===\n{summarize_document(licensing_checklist_summary, 'licensing_checklist')}",
        f"\n=== Operations Plan ===\n{summarize_document(operations_plan_summary, 'operations_plan')}",
        f"\n=== Marketing Plan ===\n{summarize_document(marketing_plan_summary, 'marketing_plan')}"
    ]
    context = "\n".join(context_parts)
    prompt = apply_readability_guidelines(EXECUTION_ROADMAP_PROMPT)
    prompt = prompt.replace("{COMPLETENESS_REQUIREMENTS}", COMPLETENESS_REQUIREMENTS)
    return f"{prompt}\n\n{context}"""

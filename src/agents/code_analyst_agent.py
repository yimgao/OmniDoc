"""
Code Analyst Agent
Analyzes codebase and generates/updates documentation from actual code
"""
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
import ast
import inspect
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.context.context_manager import ContextManager
from src.context.shared_context import AgentType, DocumentStatus, AgentOutput
from src.rate_limit.queue_manager import RequestQueue
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeAnalystAgent(BaseAgent):
    """
    Code Analyst Agent
    
    Analyzes Python codebase and generates/updates documentation:
    - Extracts classes, functions, and their docstrings
    - Analyzes code structure and dependencies
    - Generates API documentation from code
    - Updates developer documentation with actual code examples
    """
    
    def __init__(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        rate_limiter: Optional[RequestQueue] = None,
        file_manager: Optional[FileManager] = None,
        api_key: Optional[str] = None,
        **provider_kwargs
    ):
        """Initialize Code Analyst Agent"""
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        self.file_manager = file_manager or FileManager()
    
    def analyze_codebase(self, codebase_path: str) -> Dict:
        """
        Analyze codebase and extract code structure
        
        Args:
            codebase_path: Path to codebase directory (e.g., "src/")
        
        Returns:
            Dictionary with code analysis results
        """
        codebase_path = Path(codebase_path)
        if not codebase_path.exists():
            raise ValueError(f"Codebase path does not exist: {codebase_path}")
        
        analysis = {
            "modules": [],
            "classes": [],
            "functions": [],
            "imports": [],
            "file_structure": []
        }
        
        # Find all Python files
        python_files = list(codebase_path.rglob("*.py"))
        logger.info(f"Analyzing {len(python_files)} Python files in {codebase_path}")
        
        for py_file in python_files:
            try:
                # Skip __pycache__ and test files (optional)
                if "__pycache__" in str(py_file) or "test" in py_file.name.lower():
                    continue
                
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST
                try:
                    tree = ast.parse(content)
                    
                    # Extract module info
                    module_info = {
                        "file": str(py_file.relative_to(codebase_path)),
                        "classes": [],
                        "functions": [],
                        "docstring": ast.get_docstring(tree)
                    }
                    
                    # Extract classes
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_info = {
                                "name": node.name,
                                "docstring": ast.get_docstring(node),
                                "methods": [],
                                "bases": [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
                            }
                            
                            # Extract methods
                            for item in node.body:
                                if isinstance(item, ast.FunctionDef):
                                    method_info = {
                                        "name": item.name,
                                        "docstring": ast.get_docstring(item),
                                        "args": [arg.arg for arg in item.args.args],
                                        "decorators": [ast.unparse(d) if hasattr(ast, 'unparse') else str(d) for d in item.decorator_list]
                                    }
                                    class_info["methods"].append(method_info)
                            
                            module_info["classes"].append(class_info)
                            analysis["classes"].append({
                                "file": module_info["file"],
                                **class_info
                            })
                        
                    # Extract top-level functions (not inside classes)
                    for node in tree.body:
                        if isinstance(node, ast.FunctionDef):
                            func_info = {
                                "name": node.name,
                                "docstring": ast.get_docstring(node),
                                "args": [arg.arg for arg in node.args.args],
                                "file": str(py_file.relative_to(codebase_path))
                            }
                            module_info["functions"].append(func_info)
                            analysis["functions"].append(func_info)
                    
                    analysis["modules"].append(module_info)
                    analysis["file_structure"].append(str(py_file.relative_to(codebase_path)))
                    
                except SyntaxError as e:
                    logger.warning(f"Could not parse {py_file}: {e}")
                    continue
                    
            except Exception as e:
                logger.warning(f"Error analyzing {py_file}: {e}")
                continue
        
        logger.info(f"Code analysis complete: {len(analysis['modules'])} modules, {len(analysis['classes'])} classes, {len(analysis['functions'])} functions")
        return analysis
    
    def generate_code_documentation(
        self,
        code_analysis: Dict,
        existing_docs: Optional[str] = None
    ) -> str:
        """
        Generate documentation from code analysis
        
        Args:
            code_analysis: Results from analyze_codebase()
            existing_docs: Optional existing documentation to update
        
        Returns:
            Generated/updated documentation
        """
        # Format code analysis for LLM
        code_summary = f"""
# Codebase Analysis Summary

## Modules Analyzed: {len(code_analysis['modules'])}
## Classes Found: {len(code_analysis['classes'])}
## Functions Found: {len(code_analysis['functions'])}

## Key Classes:
"""
        for cls in code_analysis['classes'][:20]:  # Limit to first 20
            code_summary += f"""
### {cls['name']} (in {cls['file']})
- Docstring: {cls.get('docstring', 'No docstring')}
- Methods: {len(cls.get('methods', []))}
- Bases: {', '.join(cls.get('bases', []))}
"""
        
        code_summary += "\n## Key Functions:\n"
        for func in code_analysis['functions'][:20]:  # Limit to first 20
            code_summary += f"""
### {func['name']} (in {func['file']})
- Docstring: {func.get('docstring', 'No docstring')}
- Args: {', '.join(func.get('args', []))}
"""
        
        prompt = f"""You are a Code Documentation Specialist. Your task is to generate comprehensive API and Developer documentation based on actual codebase analysis.

CRITICAL INSTRUCTIONS:
1. Analyze the code structure provided below
2. Generate accurate API documentation based on actual classes and functions
3. Include code examples from the actual codebase
4. Document all public APIs, classes, and functions
5. If existing documentation is provided, update it to match the actual code
6. Ensure documentation is 100% accurate to the code

=== CODEBASE ANALYSIS ===

{code_summary}

=== EXISTING DOCUMENTATION (if any) ===

{existing_docs if existing_docs else "No existing documentation provided"}

=== YOUR TASK ===

Generate comprehensive API and Developer documentation that:
- Accurately reflects the actual codebase structure
- Documents all public classes and functions
- Includes code examples from the actual code
- Provides usage instructions based on real code
- Updates any outdated information from existing docs

Start with the documentation content:"""
        
        try:
            logger.debug("Generating code-based documentation")
            doc = self._call_llm(prompt, temperature=0.5)
            return doc
        except Exception as e:
            logger.error(f"Error generating code documentation: {e}")
            raise
    
    def analyze_and_update_docs(
        self,
        codebase_path: str,
        output_filename: str = "code_analysis_docs.md",
        project_id: Optional[str] = None,
        context_manager: Optional[ContextManager] = None
    ) -> str:
        """
        Analyze codebase and generate/update documentation
        
        Args:
            codebase_path: Path to codebase
            output_filename: Output filename
            project_id: Project ID
            context_manager: Context manager
        
        Returns:
            Path to generated documentation
        """
        logger.info(f"Analyzing codebase at: {codebase_path}")
        
        # Analyze codebase
        code_analysis = self.analyze_codebase(codebase_path)
        
        # Get existing docs if available
        existing_docs = None
        if project_id and context_manager:
            api_output = context_manager.get_agent_output(project_id, AgentType.API_DOCUMENTATION)
            if api_output:
                existing_docs = api_output.content
        
        # Generate documentation
        doc_content = self.generate_code_documentation(code_analysis, existing_docs)
        
        # Save to file
        file_path = self.file_manager.write_file(output_filename, doc_content, project_id=project_id)
        logger.info(f"Code-based documentation saved to: {file_path}")
        
        # Save to context
        if project_id and context_manager:
            try:
                output = AgentOutput(
                    agent_type=AgentType.API_DOCUMENTATION,  # Update API docs
                    document_type="code_analysis_docs",
                    content=doc_content,
                    file_path=file_path,
                    status=DocumentStatus.COMPLETE,
                    generated_at=datetime.now()
                )
                context_manager.save_agent_output(project_id, output)
            except Exception as e:
                logger.warning(f"Could not save to context: {e}")
        
        return file_path


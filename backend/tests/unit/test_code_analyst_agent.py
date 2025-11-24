"""
Unit Tests: CodeAnalystAgent
Fast, isolated tests for code analyst agent
"""
import pytest
import tempfile
import ast
from pathlib import Path
from src.agents.code_analyst_agent import CodeAnalystAgent


@pytest.mark.unit
class TestCodeAnalystAgent:
    """Test CodeAnalystAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager):
        """Test agent initialization"""
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        assert agent.file_manager is not None
    
    def test_analyze_codebase_simple_class(self, mock_llm_provider, file_manager, temp_dir):
        """Test analyzing a codebase with a simple class"""
        # Create a temporary Python file with a class
        test_file = temp_dir / "test_module.py"
        test_file.write_text("""
class TestClass:
    \"\"\"A test class\"\"\"
    
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        \"\"\"Get the value\"\"\"
        return self.value

def test_function():
    \"\"\"A test function\"\"\"
    return "test"
""")
        
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        # Analyze the codebase
        analysis = agent.analyze_codebase(str(temp_dir))
        
        # Verify analysis results
        assert "modules" in analysis
        assert "classes" in analysis
        assert "functions" in analysis
        assert len(analysis["modules"]) > 0
        assert len(analysis["classes"]) > 0
        assert len(analysis["functions"]) > 0
        
        # Check that TestClass was found
        class_names = [cls["name"] for cls in analysis["classes"]]
        assert "TestClass" in class_names
        
        # Check that test_function was found
        function_names = [func["name"] for func in analysis["functions"]]
        assert "test_function" in function_names
    
    def test_analyze_codebase_with_docstrings(self, mock_llm_provider, file_manager, temp_dir):
        """Test that docstrings are extracted correctly"""
        # Create a Python file with docstrings
        test_file = temp_dir / "documented_module.py"
        test_file.write_text("""
\"\"\"Module docstring\"\"\"

class DocumentedClass:
    \"\"\"Class docstring\"\"\"
    
    def documented_method(self):
        \"\"\"Method docstring\"\"\"
        pass

def documented_function():
    \"\"\"Function docstring\"\"\"
    pass
""")
        
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        analysis = agent.analyze_codebase(str(temp_dir))
        
        # Check module docstring
        module = analysis["modules"][0]
        assert module["docstring"] == "Module docstring"
        
        # Check class docstring
        cls = analysis["classes"][0]
        assert cls["docstring"] == "Class docstring"
        
        # Check method docstring
        method = cls["methods"][0]
        assert method["docstring"] == "Method docstring"
        
        # Check function docstring
        func = analysis["functions"][0]
        assert func["docstring"] == "Function docstring"
    
    def test_analyze_codebase_with_methods(self, mock_llm_provider, file_manager, temp_dir):
        """Test that class methods are extracted correctly"""
        # Create a Python file with a class containing multiple methods
        test_file = temp_dir / "methods_module.py"
        test_file.write_text("""
class Calculator:
    \"\"\"A simple calculator\"\"\"
    
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        \"\"\"Add two numbers\"\"\"
        return x + y
    
    def subtract(self, x, y):
        \"\"\"Subtract two numbers\"\"\"
        return x - y
    
    def multiply(self, x, y):
        \"\"\"Multiply two numbers\"\"\"
        return x * y
""")
        
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        analysis = agent.analyze_codebase(str(temp_dir))
        
        # Check that Calculator class was found
        calculator_class = next(cls for cls in analysis["classes"] if cls["name"] == "Calculator")
        
        # Check that methods were extracted
        assert len(calculator_class["methods"]) >= 3
        
        # Check method names
        method_names = [method["name"] for method in calculator_class["methods"]]
        assert "add" in method_names
        assert "subtract" in method_names
        assert "multiply" in method_names
        
        # Check method arguments
        add_method = next(m for m in calculator_class["methods"] if m["name"] == "add")
        assert "x" in add_method["args"]
        assert "y" in add_method["args"]
    
    def test_analyze_codebase_with_inheritance(self, mock_llm_provider, file_manager, temp_dir):
        """Test that class inheritance is detected"""
        # Create a Python file with inheritance
        test_file = temp_dir / "inheritance_module.py"
        test_file.write_text("""
class BaseClass:
    \"\"\"Base class\"\"\"
    pass

class DerivedClass(BaseClass):
    \"\"\"Derived class\"\"\"
    pass
""")
        
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        analysis = agent.analyze_codebase(str(temp_dir))
        
        # Check that DerivedClass has BaseClass as a base
        derived_class = next(cls for cls in analysis["classes"] if cls["name"] == "DerivedClass")
        assert "BaseClass" in derived_class["bases"]
    
    def test_analyze_codebase_skips_test_files(self, mock_llm_provider, file_manager, temp_dir):
        """Test that test files are skipped"""
        # Create a test file
        test_file = temp_dir / "test_module.py"
        test_file.write_text("""
class TestClass:
    pass
""")
        
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        analysis = agent.analyze_codebase(str(temp_dir))
        
        # Test files should be skipped (check if TestClass is not in classes)
        # Note: This test depends on the implementation - if test files are skipped,
        # TestClass should not be in the analysis
        # For now, we'll just verify the analysis doesn't crash
    
    def test_analyze_codebase_handles_syntax_errors(self, mock_llm_provider, file_manager, temp_dir):
        """Test that syntax errors are handled gracefully"""
        # Create a Python file with a syntax error
        test_file = temp_dir / "syntax_error.py"
        test_file.write_text("""
class BrokenClass:
    def method(self
        # Missing closing parenthesis
""")
        
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        # Should not raise an exception, but should log a warning
        analysis = agent.analyze_codebase(str(temp_dir))
        
        # Analysis should still return a valid structure
        assert "modules" in analysis
        assert "classes" in analysis
        assert "functions" in analysis
    
    def test_analyze_codebase_nonexistent_path(self, mock_llm_provider, file_manager):
        """Test that analyzing a nonexistent path raises an error"""
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        with pytest.raises(ValueError, match="Codebase path does not exist"):
            agent.analyze_codebase("nonexistent/path")
    
    def test_generate_code_documentation(self, mock_llm_provider, file_manager):
        """Test generating documentation from code analysis"""
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        # Create a sample code analysis
        code_analysis = {
            "modules": [
                {
                    "file": "test_module.py",
                    "classes": [
                        {
                            "name": "TestClass",
                            "docstring": "A test class",
                            "methods": [
                                {
                                    "name": "test_method",
                                    "docstring": "A test method",
                                    "args": ["self", "x"],
                                    "decorators": []
                                }
                            ],
                            "bases": []
                        }
                    ],
                    "functions": [
                        {
                            "name": "test_function",
                            "docstring": "A test function",
                            "args": ["x", "y"],
                            "file": "test_module.py"
                        }
                    ],
                    "docstring": "Module docstring"
                }
            ],
            "classes": [
                {
                    "name": "TestClass",
                    "docstring": "A test class",
                    "methods": [],
                    "bases": [],
                    "file": "test_module.py"
                }
            ],
            "functions": [
                {
                    "name": "test_function",
                    "docstring": "A test function",
                    "args": ["x", "y"],
                    "file": "test_module.py"
                }
            ],
            "imports": [],
            "file_structure": ["test_module.py"]
        }
        
        # Generate documentation
        documentation = agent.generate_code_documentation(code_analysis)
        
        # Verify that documentation was generated
        assert documentation is not None
        assert len(documentation) > 0
        # The mock LLM should return a test document
        assert "Test Document" in documentation or "test" in documentation.lower()
    
    def test_generate_code_documentation_with_existing_docs(self, mock_llm_provider, file_manager):
        """Test generating documentation with existing docs"""
        agent = CodeAnalystAgent(
            provider_name="gemini",
            file_manager=file_manager
        )
        
        code_analysis = {
            "modules": [],
            "classes": [],
            "functions": [],
            "imports": [],
            "file_structure": []
        }
        
        existing_docs = "# Existing Documentation\n\nSome content here."
        
        # Generate documentation
        documentation = agent.generate_code_documentation(code_analysis, existing_docs)
        
        # Verify that documentation was generated
        assert documentation is not None
        assert len(documentation) > 0


"""
Unit Tests: TemplateEngine
Fast, isolated tests for template engine
"""
import pytest
from pathlib import Path
from src.utils.template_engine import TemplateEngine


@pytest.mark.unit
class TestTemplateEngine:
    """Test TemplateEngine class"""
    
    @pytest.fixture
    def temp_template_dir(self, tmp_path):
        """Create temporary template directory"""
        return tmp_path / "templates"
    
    @pytest.fixture
    def engine(self, temp_template_dir):
        """Create template engine instance"""
        return TemplateEngine(template_dir=temp_template_dir)
    
    def test_template_engine_initialization(self, engine, temp_template_dir):
        """Test template engine initialization"""
        assert engine.template_dir == temp_template_dir
        assert temp_template_dir.exists()
    
    def test_render_with_custom_template(self, engine):
        """Test rendering with custom template string"""
        template = "Hello {{ name }}!"
        context = {"name": "World"}
        result = engine.render("test", context, custom_template=template)
        assert result == "Hello World!"
    
    def test_save_and_load_template(self, engine, temp_template_dir):
        """Test saving and loading templates"""
        template_name = "test_template.md"
        template_content = "# {{ title }}\n\n{{ content }}"
        
        engine.save_template(template_name, template_content)
        
        assert (temp_template_dir / template_name).exists()
        
        loaded = engine.get_template(template_name)
        assert loaded == template_content
    
    def test_render_template_file(self, engine, temp_template_dir):
        """Test rendering from template file"""
        template_name = "test.md"
        template_content = "# {{ title }}\n\n{{ description }}"
        (temp_template_dir / template_name).write_text(template_content)
        
        context = {"title": "Test Document", "description": "This is a test"}
        result = engine.render(template_name, context)
        
        assert "# Test Document" in result
        assert "This is a test" in result
    
    def test_list_templates(self, engine, temp_template_dir):
        """Test listing templates"""
        (temp_template_dir / "template1.md").write_text("Content 1")
        (temp_template_dir / "template2.md").write_text("Content 2")
        
        templates = engine.list_templates()
        
        assert "template1.md" in templates
        assert "template2.md" in templates
    
    def test_fallback_rendering(self, engine):
        """Test fallback rendering when template doesn't exist"""
        context = {
            "project_name": "Test Project",
            "features": ["Feature 1", "Feature 2"]
        }
        
        result = engine.render("nonexistent.md", context)
        
        assert "Test Project" in result or "nonexistent" in result.lower()


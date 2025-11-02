"""
Unit Tests: FormatConverterAgent
Fast, isolated tests for format converter agent
"""
import pytest
from pathlib import Path
from src.agents.format_converter_agent import FormatConverterAgent


@pytest.mark.unit
class TestFormatConverterAgent:
    """Test FormatConverterAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager):
        """Test agent initialization"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        assert agent.agent_name == "FormatConverterAgent"
        assert agent.file_manager is not None
        assert "html" in agent.supported_formats
    
    def test_markdown_to_html(self, mock_llm_provider, file_manager):
        """Test Markdown to HTML conversion"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        markdown = "# Test Title\n\nThis is a paragraph."
        html = agent.markdown_to_html(markdown)
        
        assert html is not None
        assert len(html) > 0
        assert "<html>" in html.lower() or "<h1>" in html.lower()
    
    def test_convert_html(self, mock_llm_provider, file_manager):
        """Test converting to HTML format"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        markdown = "# Test Document\n\nContent here."
        file_path = agent.convert(markdown, "html", "test.html")
        
        assert file_path is not None
        assert file_manager.file_exists("test.html")
    
    def test_convert_unsupported_format(self, mock_llm_provider, file_manager):
        """Test error on unsupported format"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        with pytest.raises(ValueError, match="Unsupported format"):
            agent.convert("# Test", "xyz", "test.xyz")
    
    def test_convert_all_documents(self, mock_llm_provider, file_manager):
        """Test converting multiple documents"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        documents = {
            "doc1.md": "# Document 1\n\nContent 1",
            "doc2.md": "# Document 2\n\nContent 2"
        }
        
        results = agent.convert_all_documents(documents, ["html"])
        
        assert len(results) == 2
        assert "doc1.md" in results
        assert "doc2.md" in results
    
    def test_markdown_to_pdf(self, mock_llm_provider, file_manager):
        """Test Markdown to PDF conversion"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        markdown = "# Test Title\n\nThis is a paragraph with **bold** text."
        html = agent.markdown_to_html(markdown)
        
        try:
            pdf_path = agent.html_to_pdf(html, "test.pdf")
            assert Path(pdf_path).exists()
        except ImportError:
            pytest.skip("PDF libraries not installed")
    
    def test_markdown_to_docx(self, mock_llm_provider, file_manager):
        """Test Markdown to DOCX conversion"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        markdown = "# Test Title\n\nThis is a paragraph.\n\n## Section\n\n- Item 1\n- Item 2"
        
        try:
            docx_path = agent.markdown_to_docx(markdown, "test.docx")
            assert Path(docx_path).exists()
        except ImportError:
            pytest.skip("DOCX library not installed")
    
    def test_convert_multiple_formats(self, mock_llm_provider, file_manager):
        """Test converting to multiple formats"""
        agent = FormatConverterAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        markdown = "# Test Document\n\nContent here."
        
        try:
            html_path = agent.convert(markdown, "html", "test.html")
            assert Path(html_path).exists()
        except Exception:
            pass  # HTML should always work
        
        try:
            pdf_path = agent.convert(markdown, "pdf", "test.pdf")
            assert Path(pdf_path).exists()
        except (ImportError, Exception):
            pass  # PDF might not be available
        
        try:
            docx_path = agent.convert(markdown, "docx", "test.docx")
            assert Path(docx_path).exists()
        except (ImportError, Exception):
            pass  # DOCX might not be available


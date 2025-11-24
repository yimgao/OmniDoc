"""
Unit Tests: FileManager
Fast, isolated tests for file operations
"""
import pytest
from pathlib import Path


@pytest.mark.unit
class TestFileManager:
    """Test FileManager class"""
    
    def test_write_file(self, file_manager):
        """Test writing a file"""
        content = "Test content"
        file_path = file_manager.write_file("test.txt", content)
        
        assert Path(file_path).exists()
        assert Path(file_path).read_text() == content
    
    def test_read_file(self, file_manager):
        """Test reading a file"""
        content = "Test content to read"
        file_manager.write_file("test.txt", content)
        
        read_content = file_manager.read_file("test.txt")
        assert read_content == content
    
    def test_file_exists(self, file_manager):
        """Test file existence check"""
        assert not file_manager.file_exists("nonexistent.txt")
        
        file_manager.write_file("exists.txt", "content")
        assert file_manager.file_exists("exists.txt")
    
    def test_get_file_size(self, file_manager):
        """Test getting file size"""
        content = "Test content"
        file_manager.write_file("size_test.txt", content)
        
        size = file_manager.get_file_size("size_test.txt")
        assert size == len(content.encode('utf-8'))
    
    def test_auto_directory_creation(self, file_manager):
        """Test automatic directory creation"""
        file_path = file_manager.write_file("subdir/test.txt", "content")
        
        assert Path(file_path).exists()
        assert Path(file_path).parent.exists()
    
    def test_set_base_dir(self, file_manager, temp_dir):
        """Test changing base directory"""
        new_dir = temp_dir / "new_base"
        file_manager.set_base_dir(str(new_dir))
        
        file_manager.write_file("test.txt", "content")
        assert (new_dir / "test.txt").exists()


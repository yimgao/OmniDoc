"""
File Management Utility Class
Handles all file operations in an OOP style
"""
from pathlib import Path
from typing import Optional


class FileManager:
    """Manages file operations for documentation generation"""
    
    def __init__(self, base_dir: str = "docs"):
        """
        Initialize file manager
        
        Args:
            base_dir: Base directory for all documentation files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def write_file(self, filepath: str, content: str, encoding: str = "utf-8") -> str:
        """
        Write content to file
        
        Args:
            filepath: Path where file should be written (can be relative or absolute)
            content: Content to write
            encoding: File encoding (default: utf-8)
            
        Returns:
            Absolute path to written file
            
        Raises:
            IOError: If file writing fails
        """
        path = Path(filepath)
        
        # If relative path, make it relative to base_dir
        if not path.is_absolute():
            path = self.base_dir / path
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        try:
            path.write_text(content, encoding=encoding)
            return str(path.absolute())
        except Exception as e:
            raise IOError(f"Failed to write file {path}: {str(e)}")
    
    def read_file(self, filepath: str, encoding: str = "utf-8") -> str:
        """
        Read content from file
        
        Args:
            filepath: Path to file (can be relative or absolute)
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file reading fails
        """
        path = Path(filepath)
        
        # If relative path, make it relative to base_dir
        if not path.is_absolute():
            path = self.base_dir / path
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            return path.read_text(encoding=encoding)
        except Exception as e:
            raise IOError(f"Failed to read file {path}: {str(e)}")
    
    def file_exists(self, filepath: str) -> bool:
        """
        Check if file exists
        
        Args:
            filepath: Path to file (can be relative or absolute)
            
        Returns:
            True if file exists, False otherwise
        """
        path = Path(filepath)
        if not path.is_absolute():
            path = self.base_dir / path
        return path.exists()
    
    def get_file_size(self, filepath: str) -> int:
        """
        Get file size in bytes
        
        Args:
            filepath: Path to file (can be relative or absolute)
            
        Returns:
            File size in bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(filepath)
        if not path.is_absolute():
            path = self.base_dir / path
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        return path.stat().st_size
    
    def set_base_dir(self, base_dir: str):
        """
        Change base directory
        
        Args:
            base_dir: New base directory path
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)


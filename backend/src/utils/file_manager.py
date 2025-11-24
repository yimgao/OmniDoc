"""
File Management Utility Class
Handles all file operations in an OOP style
"""
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


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
        logger.debug(f"FileManager initialized with base_dir: {self.base_dir.absolute()}")
    
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
        logger.debug(f"Creating directories if needed: {path.parent}")
        
        # Write file
        try:
            content_size = len(content.encode(encoding))
            logger.info(f"Writing file: {path} (size: {content_size} bytes, encoding: {encoding})")
            path.write_text(content, encoding=encoding)
            abs_path = str(path.absolute())
            logger.info(f"File written successfully: {abs_path}")
            return abs_path
        except Exception as e:
            logger.error(f"Failed to write file {path}: {str(e)}", exc_info=True)
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
            logger.warning(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            logger.debug(f"Reading file: {path} (encoding: {encoding})")
            content = path.read_text(encoding=encoding)
            logger.info(f"File read successfully: {path} (size: {len(content)} characters)")
            return content
        except Exception as e:
            logger.error(f"Failed to read file {path}: {str(e)}", exc_info=True)
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
        exists = path.exists()
        logger.debug(f"Checking file existence: {path} -> {exists}")
        return exists
    
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
            logger.warning(f"File not found when getting size: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        
        size = path.stat().st_size
        logger.debug(f"File size: {path} -> {size} bytes")
        return size
    
    def set_base_dir(self, base_dir: str):
        """
        Change base directory
        
        Args:
            base_dir: New base directory path
        """
        old_dir = self.base_dir
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileManager base directory changed: {old_dir} -> {self.base_dir.absolute()}")


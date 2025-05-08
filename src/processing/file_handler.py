"""
File handler for GraphRAG project.

This module provides a unified interface for handling different file types.
"""
import os
from typing import Dict, Any, Tuple, List

# Import loaders
from ..loaders.markdown_loader import MarkdownLoader
from ..loaders.pdf_loader import PDFLoader

class FileHandler:
    """
    Handler for different file types.
    """
    
    # Map file extensions to loaders
    LOADERS = {
        ".md": MarkdownLoader,
        ".pdf": PDFLoader,
        # Add more loaders as needed
    }
    
    @staticmethod
    def get_supported_extensions() -> List[str]:
        """
        Get a list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return list(FileHandler.LOADERS.keys())
    
    @staticmethod
    def can_handle_file(file_path: str) -> bool:
        """
        Check if a file can be handled.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file can be handled
        """
        _, ext = os.path.splitext(file_path.lower())
        return ext in FileHandler.LOADERS
    
    @staticmethod
    def process_file(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process a file and extract text and metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (text, metadata)
            
        Raises:
            ValueError: If the file type is not supported
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext not in FileHandler.LOADERS:
            raise ValueError(f"Unsupported file type: {ext}")
        
        loader = FileHandler.LOADERS[ext]
        return loader.load(file_path)
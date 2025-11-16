"""
File Storage Utility - Manages claim document storage
Organizes files by claim_id in a structured folder hierarchy
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid


class FileStorage:
    """Manages file storage for claims documents"""
    
    def __init__(self, base_dir: str = "claims"):
        """
        Initialize file storage
        
        Args:
            base_dir: Base directory for storing claims (default: "claims")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_claim_dir(self, claim_id: str) -> Path:
        """Get the directory path for a specific claim"""
        claim_dir = self.base_dir / claim_id / "documents"
        claim_dir.mkdir(parents=True, exist_ok=True)
        return claim_dir
    
    def save_file(self, claim_id: str, file_content: bytes, filename: str) -> str:
        """
        Save a file for a claim
        
        Args:
            claim_id: The claim ID
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to saved file (relative to base_dir)
        """
        claim_dir = self.get_claim_dir(claim_id)
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_parts = Path(safe_filename)
        new_filename = f"{timestamp}_{name_parts.stem}{name_parts.suffix}"
        
        file_path = claim_dir / new_filename
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Return relative path from base_dir
        return str(file_path.relative_to(self.base_dir))
    
    def get_claim_documents(self, claim_id: str) -> List[str]:
        """
        Get all document paths for a claim
        
        Args:
            claim_id: The claim ID
            
        Returns:
            List of document file paths (relative to base_dir)
        """
        claim_dir = self.get_claim_dir(claim_id)
        
        if not claim_dir.exists():
            return []
        
        documents = []
        for file_path in claim_dir.iterdir():
            if file_path.is_file():
                # Return relative path from base_dir
                documents.append(str(file_path.relative_to(self.base_dir)))
        
        return sorted(documents)
    
    def get_absolute_paths(self, claim_id: str) -> List[str]:
        """
        Get absolute file paths for claim documents
        
        Args:
            claim_id: The claim ID
            
        Returns:
            List of absolute file paths
        """
        claim_dir = self.get_claim_dir(claim_id)
        
        if not claim_dir.exists():
            return []
        
        documents = []
        for file_path in claim_dir.iterdir():
            if file_path.is_file():
                documents.append(str(file_path.absolute()))
        
        return sorted(documents)
    
    def delete_claim_files(self, claim_id: str) -> bool:
        """
        Delete all files for a claim
        
        Args:
            claim_id: The claim ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            claim_base_dir = self.base_dir / claim_id
            if claim_base_dir.exists():
                shutil.rmtree(claim_base_dir)
            return True
        except Exception:
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and invalid characters"""
        # Remove path components
        filename = Path(filename).name
        
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name_parts = Path(filename)
            filename = f"{name_parts.stem[:200]}{name_parts.suffix}"
        
        return filename
    
    def file_exists(self, claim_id: str, filename: str) -> bool:
        """Check if a file exists for a claim"""
        claim_dir = self.get_claim_dir(claim_id)
        file_path = claim_dir / filename
        return file_path.exists()
    
    def migrate_claim_files(self, source_claim_id: str, target_claim_id: str) -> List[str]:
        """
        Migrate files from one claim ID to another
        
        Args:
            source_claim_id: Source claim ID (e.g., TEMP-{timestamp})
            target_claim_id: Target claim ID (e.g., CLM-{id})
            
        Returns:
            List of migrated file paths
        """
        try:
            source_dir = self.get_claim_dir(source_claim_id)
            target_dir = self.get_claim_dir(target_claim_id)
            
            if not source_dir.exists():
                return []
            
            migrated_files = []
            for file_path in source_dir.iterdir():
                if file_path.is_file():
                    # Copy file to target directory
                    target_file = target_dir / file_path.name
                    shutil.copy2(file_path, target_file)
                    
                    # Get relative path
                    relative_path = str(target_file.relative_to(self.base_dir))
                    migrated_files.append(relative_path)
            
            # Optionally remove source directory after migration
            # shutil.rmtree(source_dir)
            
            return migrated_files
        except Exception as e:
            print(f"Error migrating files: {e}")
            return []


# Global instance
file_storage = FileStorage()


"""
Script Storage Service
Handles persistence and retrieval of generated scripts
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger


class ScriptStorage:
    """
    Service for storing and retrieving generated scripts
    
    Scripts are stored as JSON files in the storage/scripts directory.
    Each script has a unique ID and contains metadata like subject, keywords, etc.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize script storage
        
        Args:
            storage_path: Path to scripts storage directory.
                         Defaults to /MoneyPrinterTurbo/storage/scripts
        """
        if storage_path is None:
            storage_path = os.environ.get(
                "MPT_STORAGE_PATH", 
                "/MoneyPrinterTurbo/storage"
            )
        
        self.scripts_dir = Path(storage_path) / "scripts"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Script storage initialized at: {self.scripts_dir}")
    
    def save_script(
        self,
        subject: str,
        script: str,
        keywords: List[str] = None,
        language: str = "en",
        paragraph_number: int = 1,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Save a generated script
        
        Args:
            subject: Video subject/topic
            script: Generated script text
            keywords: List of keywords/search terms
            language: Script language
            paragraph_number: Number of paragraphs
            metadata: Additional metadata
            
        Returns:
            script_id: Unique identifier for the saved script
        """
        # Generate unique script ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        script_id = f"scr_{timestamp}"
        
        # Create script record
        script_data = {
            "script_id": script_id,
            "subject": subject,
            "script": script,
            "keywords": keywords or [],
            "language": language,
            "paragraph_number": paragraph_number,
            "generated_at": datetime.now().isoformat(),
            "status": "draft",  # draft | used | abandoned
            "task_ids": [],  # Links to created video tasks
            "edited": False,
            "metadata": metadata or {}
        }
        
        # Save to file
        script_file = self.scripts_dir / f"{script_id}.json"
        try:
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Script saved: {script_id} - {subject}")
            return script_id
        
        except Exception as e:
            logger.error(f"Failed to save script {script_id}: {e}")
            raise
    
    def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a script by ID
        
        Args:
            script_id: Script identifier
            
        Returns:
            Script data dictionary, or None if not found
        """
        script_file = self.scripts_dir / f"{script_id}.json"
        
        if not script_file.exists():
            logger.warning(f"Script not found: {script_id}")
            return None
        
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"Failed to load script {script_id}: {e}")
            return None
    
    def list_scripts(
        self,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all scripts with optional filtering
        
        Args:
            status: Filter by status (draft/used/abandoned)
            limit: Maximum number of scripts to return
            offset: Number of scripts to skip
            
        Returns:
            List of script dictionaries, sorted by generation time (newest first)
        """
        scripts = []
        
        try:
            # Get all script files
            script_files = sorted(
                self.scripts_dir.glob("scr_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Load and filter scripts
            for script_file in script_files:
                try:
                    with open(script_file, 'r', encoding='utf-8') as f:
                        script = json.load(f)
                    
                    # Filter by status if specified
                    if status and script.get("status") != status:
                        continue
                    
                    scripts.append(script)
                
                except Exception as e:
                    logger.error(f"Failed to load script from {script_file}: {e}")
                    continue
            
            # Apply pagination
            return scripts[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Failed to list scripts: {e}")
            return []
    
    def update_script(
        self,
        script_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update script fields
        
        Args:
            script_id: Script identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        script = self.get_script(script_id)
        if not script:
            return False
        
        try:
            # Update fields
            script.update(updates)
            
            # Mark as edited if script text changed
            if "script" in updates:
                script["edited"] = True
            
            # Save updated script
            script_file = self.scripts_dir / f"{script_id}.json"
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Script updated: {script_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update script {script_id}: {e}")
            return False
    
    def delete_script(self, script_id: str) -> bool:
        """
        Delete a script
        
        Args:
            script_id: Script identifier
            
        Returns:
            True if successful, False otherwise
        """
        script_file = self.scripts_dir / f"{script_id}.json"
        
        if not script_file.exists():
            logger.warning(f"Script not found for deletion: {script_id}")
            return False
        
        try:
            script_file.unlink()
            logger.info(f"Script deleted: {script_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete script {script_id}: {e}")
            return False
    
    def mark_as_used(self, script_id: str, task_id: str) -> bool:
        """
        Mark a script as used for video creation
        
        Args:
            script_id: Script identifier
            task_id: Associated task identifier
            
        Returns:
            True if successful, False otherwise
        """
        script = self.get_script(script_id)
        if not script:
            return False
        
        # Update status and add task link
        script["status"] = "used"
        if task_id not in script["task_ids"]:
            script["task_ids"].append(task_id)
        
        return self.update_script(script_id, script)
    
    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """
        Search scripts by subject or keywords
        
        Args:
            query: Search query string
            
        Returns:
            List of matching scripts
        """
        all_scripts = self.list_scripts(limit=1000)
        query_lower = query.lower()
        
        matching_scripts = []
        for script in all_scripts:
            # Search in subject
            if query_lower in script.get("subject", "").lower():
                matching_scripts.append(script)
                continue
            
            # Search in keywords
            keywords = script.get("keywords", [])
            if any(query_lower in str(kw).lower() for kw in keywords):
                matching_scripts.append(script)
                continue
            
            # Search in script text
            if query_lower in script.get("script", "").lower():
                matching_scripts.append(script)
        
        return matching_scripts
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored scripts
        
        Returns:
            Dictionary with statistics (total, by status, etc.)
        """
        all_scripts = self.list_scripts(limit=10000)
        
        stats = {
            "total": len(all_scripts),
            "draft": 0,
            "used": 0,
            "abandoned": 0,
            "edited": 0,
        }
        
        for script in all_scripts:
            status = script.get("status", "draft")
            stats[status] = stats.get(status, 0) + 1
            
            if script.get("edited", False):
                stats["edited"] += 1
        
        return stats


# Global instance
_storage = None

def get_script_storage():
    """
    Get or create global script storage instance
    
    SWITCHABLE BACKEND:
    - Use SQLite for production (fast, scalable, FTS)
    - Use JSON for development/testing (simple, debuggable)
    """
    global _storage
    if _storage is None:
        # Import here to avoid circular dependencies
        import os
        
        # Check environment variable or auto-detect
        use_sqlite = os.getenv("USE_SQLITE_STORAGE", "true").lower() == "true"
        
        if use_sqlite:
            try:
                from webui.services.script_storage_sqlite import ScriptStorageSQLite
                _storage = ScriptStorageSQLite()
                logger.info("Using SQLite storage backend")
            except ImportError as e:
                logger.warning(f"Failed to import SQLite storage, falling back to JSON: {e}")
                _storage = ScriptStorage()
        else:
            _storage = ScriptStorage()
            logger.info("Using JSON file storage backend")
    
    return _storage

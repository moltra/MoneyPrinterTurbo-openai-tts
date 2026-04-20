"""
SQLite-based Script Storage Service
High-performance, scalable storage with full-text search
"""
import sqlite3
import orjson
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
from contextlib import contextmanager


class ScriptStorageSQLite:
    """
    SQLite-based storage for video scripts with full-text search
    
    Features:
    - Fast queries with indexes
    - Full-text search (FTS5)
    - ACID transactions
    - Handles 10,000+ scripts easily
    """
    
    def __init__(self, db_path: str = "/MoneyPrinterTurbo/storage/scripts.db"):
        """
        Initialize SQLite storage
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._create_tables()
        
        logger.info(f"Script storage (SQLite) initialized at: {db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main scripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scripts (
                    script_id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    script TEXT NOT NULL,
                    keywords TEXT,  -- JSON array
                    language TEXT DEFAULT 'en',
                    paragraph_number INTEGER DEFAULT 1,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'draft',
                    edited BOOLEAN DEFAULT 0,
                    metadata TEXT  -- JSON object
                )
            """)
            
            # Script-task linking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS script_tasks (
                    script_id TEXT,
                    task_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (script_id, task_id),
                    FOREIGN KEY (script_id) REFERENCES scripts(script_id) ON DELETE CASCADE
                )
            """)
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scripts_status ON scripts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scripts_generated_at ON scripts(generated_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scripts_subject ON scripts(subject)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_script_tasks_task_id ON script_tasks(task_id)")
            
            # Full-text search table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS scripts_fts USING fts5(
                    script_id UNINDEXED,
                    subject,
                    script,
                    keywords,
                    content=scripts,
                    content_rowid=rowid
                )
            """)
            
            # Triggers to keep FTS in sync
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS scripts_ai AFTER INSERT ON scripts BEGIN
                    INSERT INTO scripts_fts(script_id, subject, script, keywords)
                    VALUES (new.script_id, new.subject, new.script, new.keywords);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS scripts_ad AFTER DELETE ON scripts BEGIN
                    DELETE FROM scripts_fts WHERE script_id = old.script_id;
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS scripts_au AFTER UPDATE ON scripts BEGIN
                    UPDATE scripts_fts 
                    SET subject = new.subject, 
                        script = new.script,
                        keywords = new.keywords
                    WHERE script_id = old.script_id;
                END
            """)
    
    def save_script(
        self,
        subject: str,
        script: str,
        keywords: List[str],
        language: str = "en",
        paragraph_number: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a new script
        
        Args:
            subject: Video subject
            script: Generated script text
            keywords: List of search keywords
            language: Script language
            paragraph_number: Number of paragraphs
            metadata: Additional metadata
            
        Returns:
            script_id: Unique identifier for the script
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        script_id = f"scr_{timestamp}"
        
        keywords_json = orjson.dumps(keywords).decode('utf-8')
        metadata_json = orjson.dumps(metadata or {}).decode('utf-8')
        
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO scripts (
                        script_id, subject, script, keywords, language,
                        paragraph_number, status, edited, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    script_id, subject, script, keywords_json, language,
                    paragraph_number, 'draft', False, metadata_json
                ))
            
            logger.info(f"Saved script: {script_id}")
            return script_id
        
        except Exception as e:
            logger.error(f"Failed to save script: {e}")
            raise
    
    def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a script by ID
        
        Args:
            script_id: Script identifier
            
        Returns:
            Script data dict or None if not found
        """
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM scripts WHERE script_id = ?",
                    (script_id,)
                ).fetchone()
                
                if not row:
                    return None
                
                # Convert to dict and parse JSON fields
                script = dict(row)
                script['keywords'] = orjson.loads(script['keywords'])
                script['metadata'] = orjson.loads(script['metadata'])
                script['edited'] = bool(script['edited'])
                
                # Get linked tasks
                tasks = conn.execute(
                    "SELECT task_id FROM script_tasks WHERE script_id = ?",
                    (script_id,)
                ).fetchall()
                script['task_ids'] = [t['task_id'] for t in tasks]
                
                return script
        
        except Exception as e:
            logger.error(f"Failed to get script {script_id}: {e}")
            return None
    
    def list_scripts(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List scripts with optional filtering
        
        Args:
            status: Filter by status (draft/used/abandoned)
            limit: Maximum number of scripts to return
            offset: Number of scripts to skip
            
        Returns:
            List of script dictionaries
        """
        try:
            with self._get_connection() as conn:
                if status:
                    query = """
                        SELECT * FROM scripts 
                        WHERE status = ?
                        ORDER BY generated_at DESC
                        LIMIT ? OFFSET ?
                    """
                    rows = conn.execute(query, (status, limit, offset)).fetchall()
                else:
                    query = """
                        SELECT * FROM scripts 
                        ORDER BY generated_at DESC
                        LIMIT ? OFFSET ?
                    """
                    rows = conn.execute(query, (limit, offset)).fetchall()
                
                scripts = []
                for row in rows:
                    script = dict(row)
                    script['keywords'] = orjson.loads(script['keywords'])
                    script['metadata'] = orjson.loads(script['metadata'])
                    script['edited'] = bool(script['edited'])
                    
                    # Get linked tasks
                    tasks = conn.execute(
                        "SELECT task_id FROM script_tasks WHERE script_id = ?",
                        (script['script_id'],)
                    ).fetchall()
                    script['task_ids'] = [t['task_id'] for t in tasks]
                    
                    scripts.append(script)
                
                return scripts
        
        except Exception as e:
            logger.error(f"Failed to list scripts: {e}")
            return []
    
    def update_script(self, script_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a script
        
        Args:
            script_id: Script identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Mark as edited if script content changed
            if 'script' in updates:
                updates['edited'] = True
            
            # Add updated timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            # Build update query
            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [script_id]
            
            with self._get_connection() as conn:
                conn.execute(
                    f"UPDATE scripts SET {set_clause} WHERE script_id = ?",
                    values
                )
            
            logger.info(f"Updated script: {script_id}")
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
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM scripts WHERE script_id = ?", (script_id,))
            
            logger.info(f"Deleted script: {script_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete script {script_id}: {e}")
            return False
    
    def mark_as_used(self, script_id: str, task_id: str) -> bool:
        """
        Mark script as used and link to task
        
        Args:
            script_id: Script identifier
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                # Update script status
                conn.execute(
                    "UPDATE scripts SET status = 'used' WHERE script_id = ?",
                    (script_id,)
                )
                
                # Link to task (ignore if already exists)
                conn.execute("""
                    INSERT OR IGNORE INTO script_tasks (script_id, task_id)
                    VALUES (?, ?)
                """, (script_id, task_id))
            
            logger.info(f"Marked script {script_id} as used by task {task_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to mark script as used: {e}")
            return False
    
    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """
        Full-text search for scripts
        
        Args:
            query: Search query
            
        Returns:
            List of matching scripts
        """
        try:
            with self._get_connection() as conn:
                # Use FTS5 for fast full-text search
                rows = conn.execute("""
                    SELECT s.* FROM scripts s
                    INNER JOIN scripts_fts fts ON s.script_id = fts.script_id
                    WHERE scripts_fts MATCH ?
                    ORDER BY rank
                """, (query,)).fetchall()
                
                scripts = []
                for row in rows:
                    script = dict(row)
                    script['keywords'] = orjson.loads(script['keywords'])
                    script['metadata'] = orjson.loads(script['metadata'])
                    script['edited'] = bool(script['edited'])
                    
                    # Get linked tasks
                    tasks = conn.execute(
                        "SELECT task_id FROM script_tasks WHERE script_id = ?",
                        (script['script_id'],)
                    ).fetchall()
                    script['task_ids'] = [t['task_id'] for t in tasks]
                    
                    scripts.append(script)
                
                return scripts
        
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get script statistics
        
        Returns:
            Dictionary with counts by status and other metrics
        """
        try:
            with self._get_connection() as conn:
                # Total count
                total = conn.execute("SELECT COUNT(*) as count FROM scripts").fetchone()['count']
                
                # Count by status
                draft = conn.execute(
                    "SELECT COUNT(*) as count FROM scripts WHERE status = 'draft'"
                ).fetchone()['count']
                
                used = conn.execute(
                    "SELECT COUNT(*) as count FROM scripts WHERE status = 'used'"
                ).fetchone()['count']
                
                abandoned = conn.execute(
                    "SELECT COUNT(*) as count FROM scripts WHERE status = 'abandoned'"
                ).fetchone()['count']
                
                # Edited count
                edited = conn.execute(
                    "SELECT COUNT(*) as count FROM scripts WHERE edited = 1"
                ).fetchone()['count']
                
                return {
                    "total": total,
                    "draft": draft,
                    "used": used,
                    "abandoned": abandoned,
                    "edited": edited
                }
        
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"total": 0, "draft": 0, "used": 0, "abandoned": 0, "edited": 0}


# Global instance
_storage: Optional[ScriptStorageSQLite] = None


def get_script_storage() -> ScriptStorageSQLite:
    """
    Get or create global script storage instance
    
    Returns:
        ScriptStorageSQLite instance
    """
    global _storage
    if _storage is None:
        _storage = ScriptStorageSQLite()
    return _storage

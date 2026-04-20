#!/usr/bin/env python3
"""
Migration Script: JSON Files → SQLite Database
Migrates all existing JSON script files to SQLite database
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webui.services.script_storage import ScriptStorage
from webui.services.script_storage_sqlite import ScriptStorageSQLite
from loguru import logger


def migrate():
    """Migrate all JSON scripts to SQLite"""
    
    logger.info("=" * 60)
    logger.info("Starting migration: JSON → SQLite")
    logger.info("=" * 60)
    
    # Initialize both storage systems
    json_storage = ScriptStorage()
    sqlite_storage = ScriptStorageSQLite()
    
    # Get all scripts from JSON
    logger.info("Reading JSON scripts...")
    json_scripts = json_storage.list_scripts(limit=10000)
    
    if not json_scripts:
        logger.info("No scripts found in JSON storage. Nothing to migrate.")
        return
    
    logger.info(f"Found {len(json_scripts)} scripts to migrate")
    
    # Migrate each script
    migrated = 0
    failed = 0
    
    for i, script in enumerate(json_scripts, 1):
        script_id = script.get('script_id', '')
        subject = script.get('subject', 'Untitled')
        
        try:
            # Check if already exists in SQLite
            existing = sqlite_storage.get_script(script_id)
            if existing:
                logger.info(f"[{i}/{len(json_scripts)}] Skipping {script_id} (already exists)")
                continue
            
            # Insert into SQLite with original script_id and timestamps
            with sqlite_storage._get_connection() as conn:
                import orjson
                
                keywords_json = orjson.dumps(script.get('keywords', [])).decode('utf-8')
                metadata_json = orjson.dumps(script.get('metadata', {})).decode('utf-8')
                
                conn.execute("""
                    INSERT INTO scripts (
                        script_id, subject, script, keywords, language,
                        paragraph_number, generated_at, updated_at, status, edited, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    script_id,
                    script.get('subject', ''),
                    script.get('script', ''),
                    keywords_json,
                    script.get('language', 'en'),
                    script.get('paragraph_number', 1),
                    script.get('generated_at', ''),
                    script.get('generated_at', ''),  # Use generated_at as updated_at
                    script.get('status', 'draft'),
                    script.get('edited', False),
                    metadata_json
                ))
                
                # Migrate task links
                for task_id in script.get('task_ids', []):
                    conn.execute("""
                        INSERT OR IGNORE INTO script_tasks (script_id, task_id)
                        VALUES (?, ?)
                    """, (script_id, task_id))
            
            logger.info(f"[{i}/{len(json_scripts)}] ✓ Migrated: {subject[:50]}")
            migrated += 1
        
        except Exception as e:
            logger.error(f"[{i}/{len(json_scripts)}] ✗ Failed to migrate {script_id}: {e}")
            failed += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)
    logger.info(f"Total scripts: {len(json_scripts)}")
    logger.info(f"Migrated: {migrated}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped: {len(json_scripts) - migrated - failed}")
    
    # Verify SQLite statistics
    stats = sqlite_storage.get_statistics()
    logger.info("=" * 60)
    logger.info("SQLite Database Statistics:")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  Draft: {stats['draft']}")
    logger.info(f"  Used: {stats['used']}")
    logger.info(f"  Abandoned: {stats['abandoned']}")
    logger.info(f"  Edited: {stats['edited']}")
    logger.info("=" * 60)
    
    if failed == 0:
        logger.success("✓ All scripts migrated successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Verify SQLite database:")
        logger.info("   sqlite3 /MoneyPrinterTurbo/storage/scripts.db 'SELECT COUNT(*) FROM scripts;'")
        logger.info("2. Update webui/services/script_storage.py to use SQLite")
        logger.info("3. Restart containers")
        logger.info("4. Backup JSON files:")
        logger.info("   mv /MoneyPrinterTurbo/storage/scripts /MoneyPrinterTurbo/storage/scripts.backup")
    else:
        logger.warning(f"⚠ {failed} scripts failed to migrate. Check logs above.")


if __name__ == "__main__":
    migrate()

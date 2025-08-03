#!/usr/bin/env python3
"""
Script to clear all offline stored files and tasks
"""

import os
import shutil
import sqlite3
from pathlib import Path

def clear_offline_storage():
    """Clear all offline stored files and database entries"""
    
    # Paths
    uploads_dir = Path("uploads")
    offload_dir = Path("offload")
    db_file = Path("rapidcare_offline.db")
    
    print("🧹 Clearing offline storage...")
    
    # 1. Clear uploads directory
    if uploads_dir.exists():
        for file in uploads_dir.glob("*"):
            if file.is_file():
                file.unlink()
                print(f"🗑️  Deleted: {file}")
        print(f"✅ Cleared uploads directory")
    else:
        print("ℹ️  Uploads directory doesn't exist")
    
    # 2. Clear offload directory
    if offload_dir.exists():
        for file in offload_dir.glob("*"):
            if file.is_file():
                file.unlink()
                print(f"🗑️  Deleted: {file}")
        print(f"✅ Cleared offload directory")
    else:
        print("ℹ️  Offload directory doesn't exist")
    
    # 3. Clear database entries
    if db_file.exists():
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Clear offline tasks table
            cursor.execute("DELETE FROM offline_tasks")
            tasks_deleted = cursor.rowcount
            
            # Clear any other relevant tables
            cursor.execute("DELETE FROM processed_files")
            files_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"🗑️  Deleted {tasks_deleted} offline tasks from database")
            print(f"🗑️  Deleted {files_deleted} processed files from database")
            print("✅ Cleared database entries")
            
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
    else:
        print("ℹ️  Database file doesn't exist")
    
    print("\n🎉 Offline storage cleared successfully!")
    print("📁 All stored files and tasks have been removed")

if __name__ == "__main__":
    clear_offline_storage() 
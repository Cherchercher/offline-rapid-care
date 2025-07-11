#!/usr/bin/env python3
"""
Script to flush the vector database
"""

import shutil
import os

def flush_vector_database():
    """Flush the vector database by removing the vector_db directory"""
    try:
        vector_db_path = "./vector_db"
        
        if os.path.exists(vector_db_path):
            print(f"🗑️  Removing vector database at: {vector_db_path}")
            shutil.rmtree(vector_db_path)
            print("✅ Vector database flushed successfully")
        else:
            print("ℹ️  Vector database directory doesn't exist")
        
        print("🔄 Next time the app starts, it will recreate the vector database with proper image paths")
        
    except Exception as e:
        print(f"❌ Error flushing vector database: {e}")

if __name__ == "__main__":
    flush_vector_database() 
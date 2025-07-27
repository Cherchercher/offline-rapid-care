#!/usr/bin/env python3
"""
Offline Storage Manager for Jetson Devices
Handles data persistence when offline and syncs when connectivity returns
"""

import os
import json
import sqlite3
import shutil
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass, asdict
import uuid

@dataclass
class OfflineTask:
    """Represents a task that was processed offline"""
    id: str
    task_type: str  # 'audio', 'image', 'video'
    file_path: str
    original_filename: str
    timestamp: float
    processed: bool = False
    result: Optional[Dict] = None
    error: Optional[str] = None
    synced: bool = False
    metadata: Optional[Dict] = None

class OfflineStorageManager:
    """Manages offline data storage and sync for Jetson devices"""
    
    def __init__(self, base_dir: str = "./offline_storage"):
        self.base_dir = Path(base_dir)
        self.offline_dir = self.base_dir / "pending"
        self.processed_dir = self.base_dir / "processed"
        self.db_path = self.base_dir / "offline_tasks.db"
        
        # Create directories
        self.offline_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Start sync thread
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
        print(f"🚀 Offline Storage Manager initialized at {self.base_dir}")
    
    def _init_database(self):
        """Initialize SQLite database for tracking offline tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                timestamp REAL NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                result TEXT,
                error TEXT,
                synced BOOLEAN DEFAULT FALSE,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_offline_task(self, task_type: str, file_path: str, original_filename: str, 
                          metadata: Optional[Dict] = None) -> str:
        """
        Store a file for offline processing
        
        Args:
            task_type: Type of task ('audio', 'image', 'video')
            file_path: Path to the uploaded file
            original_filename: Original filename
            metadata: Additional metadata
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Copy file to offline storage
        source_path = Path(file_path)
        if source_path.exists():
            # Create subdirectory by type
            type_dir = self.offline_dir / task_type
            type_dir.mkdir(exist_ok=True)
            
            # Copy file with task ID
            dest_path = type_dir / f"{task_id}_{original_filename}"
            shutil.copy2(source_path, dest_path)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO offline_tasks 
                (id, task_type, file_path, original_filename, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task_id, task_type, str(dest_path), original_filename, 
                timestamp, json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
            conn.close()
            
            print(f"💾 Stored offline task {task_id} ({task_type}): {original_filename}")
            return task_id
        else:
            raise FileNotFoundError(f"Source file not found: {file_path}")
    
    def get_pending_tasks(self, task_type: Optional[str] = None) -> List[OfflineTask]:
        """Get list of pending offline tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if task_type:
            cursor.execute('''
                SELECT id, task_type, file_path, original_filename, timestamp, 
                       processed, result, error, synced, metadata
                FROM offline_tasks 
                WHERE task_type = ? AND processed = FALSE
                ORDER BY timestamp
            ''', (task_type,))
        else:
            cursor.execute('''
                SELECT id, task_type, file_path, original_filename, timestamp, 
                       processed, result, error, synced, metadata
                FROM offline_tasks 
                WHERE processed = FALSE
                ORDER BY timestamp
            ''')
        
        tasks = []
        for row in cursor.fetchall():
            task = OfflineTask(
                id=row[0],
                task_type=row[1],
                file_path=row[2],
                original_filename=row[3],
                timestamp=row[4],
                processed=bool(row[5]),
                result=json.loads(row[6]) if row[6] else None,
                error=row[7],
                synced=bool(row[8]),
                metadata=json.loads(row[9]) if row[9] else None
            )
            tasks.append(task)
        
        conn.close()
        return tasks
    
    def mark_task_processed(self, task_id: str, result: Dict, error: Optional[str] = None):
        """Mark a task as processed with results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE offline_tasks 
            SET processed = TRUE, result = ?, error = ?
            WHERE id = ?
        ''', (json.dumps(result), error, task_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Marked task {task_id} as processed")
    
    def mark_task_synced(self, task_id: str):
        """Mark a task as synced to cloud"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE offline_tasks 
            SET synced = TRUE
            WHERE id = ?
        ''', (task_id,))
        
        conn.commit()
        conn.close()
        
        print(f"☁️ Marked task {task_id} as synced")
    
    def is_online(self) -> bool:
        """Check if internet connectivity is available"""
        try:
            # Try to connect to a reliable service
            response = requests.get("https://httpbin.org/get", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_jetson_device(self) -> bool:
        """Check if running on a Jetson device"""
        try:
            # Check for Jetson-specific files
            jetson_indicators = [
                "/etc/nv_tegra_release",  # Tegra release file
                "/proc/device-tree/model",  # Device tree model
                "/sys/module/tegra_fuse/parameters/tegra_chip_id"  # Tegra chip ID
            ]
            
            for indicator in jetson_indicators:
                if os.path.exists(indicator):
                    return True
            
            # Check if CUDA is available (indicates GPU capability)
            import torch
            if torch.cuda.is_available():
                # Additional check for Jetson-specific CUDA properties
                try:
                    device_count = torch.cuda.device_count()
                    if device_count > 0:
                        device_name = torch.cuda.get_device_name(0).lower()
                        if 'tegra' in device_name or 'jetson' in device_name:
                            return True
                except:
                    pass
            
            return False
        except:
            return False
    
    def get_device_capabilities(self) -> Dict:
        """Get device capabilities for offline processing"""
        import torch
        
        capabilities = {
            "is_jetson": self.is_jetson_device(),
            "has_cuda": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "memory_available": None,
            "offline_processing_supported": False
        }
        
        # Check memory availability
        try:
            import psutil
            capabilities["memory_available"] = psutil.virtual_memory().available / (1024**3)  # GB
        except:
            pass
        
        # Determine if offline processing is supported
        if capabilities["is_jetson"]:
            capabilities["offline_processing_supported"] = True
        elif capabilities["has_cuda"] and capabilities["memory_available"] and capabilities["memory_available"] > 4:
            # Allow offline processing on high-end GPUs with sufficient memory
            capabilities["offline_processing_supported"] = True
        else:
            # CPU-only or insufficient memory
            capabilities["offline_processing_supported"] = False
        
        return capabilities
    
    def _sync_worker(self):
        """Background worker that syncs processed tasks when online"""
        while True:
            try:
                if self.is_online():
                    self._sync_pending_tasks()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"❌ Error in sync worker: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _sync_pending_tasks(self):
        """Sync processed tasks to cloud when online"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get processed but not synced tasks
        cursor.execute('''
            SELECT id, task_type, file_path, original_filename, timestamp, 
                   result, metadata
            FROM offline_tasks 
            WHERE processed = TRUE AND synced = FALSE
        ''')
        
        tasks_to_sync = cursor.fetchall()
        conn.close()
        
        if tasks_to_sync:
            print(f"🔄 Syncing {len(tasks_to_sync)} processed tasks...")
            
            for task_data in tasks_to_sync:
                task_id, task_type, file_path, original_filename, timestamp, result, metadata = task_data
                
                try:
                    # Here you would implement the actual cloud sync
                    # For now, we'll just mark as synced
                    self._sync_task_to_cloud(task_id, task_type, file_path, result, metadata)
                    self.mark_task_synced(task_id)
                    
                except Exception as e:
                    print(f"❌ Failed to sync task {task_id}: {e}")
    
    def _sync_task_to_cloud(self, task_id: str, task_type: str, file_path: str, 
                           result: Dict, metadata: Optional[Dict]):
        """
        Sync a task to cloud storage
        This is a placeholder - implement your cloud sync logic here
        """
        # Example cloud sync implementation:
        # - Upload file to cloud storage (S3, Google Cloud, etc.)
        # - Send results to your backend API
        # - Update patient records in cloud database
        
        print(f"☁️ Syncing {task_type} task {task_id} to cloud...")
        print(f"   File: {file_path}")
        print(f"   Result: {result}")
        
        # Placeholder for actual cloud sync
        # You would implement:
        # 1. Upload file to cloud storage
        # 2. Send results to your API
        # 3. Update patient records
        pass
    
    def process_offline_tasks(self, model_manager):
        """Process all pending offline tasks"""
        pending_tasks = self.get_pending_tasks()
        
        if not pending_tasks:
            print("📭 No pending offline tasks to process")
            return
        
        print(f"🔄 Processing {len(pending_tasks)} offline tasks...")
        
        for task in pending_tasks:
            try:
                print(f"🔄 Processing {task.task_type} task: {task.original_filename}")
                
                # Process based on task type
                if task.task_type == "audio":
                    result = self._process_offline_audio(task, model_manager)
                elif task.task_type == "image":
                    result = self._process_offline_image(task, model_manager)
                elif task.task_type == "video":
                    result = self._process_offline_video(task, model_manager)
                else:
                    raise ValueError(f"Unknown task type: {task.task_type}")
                
                # Mark as processed
                self.mark_task_processed(task.id, result)
                
            except Exception as e:
                print(f"❌ Failed to process task {task.id}: {e}")
                self.mark_task_processed(task.id, {}, str(e))
    
    def _process_offline_audio(self, task: OfflineTask, model_manager) -> Dict:
        """Process offline audio task"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio": task.file_path},
                    {"type": "text", "text": "Transcribe this audio and extract any medical information."}
                ]
            }
        ]
        
        result = model_manager.chat_audio(messages)
        return result
    
    def _process_offline_image(self, task: OfflineTask, model_manager) -> Dict:
        """Process offline image task"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": task.file_path},
                    {"type": "text", "text": "Analyze this image for medical triage assessment."}
                ]
            }
        ]
        
        result = model_manager.chat_image(messages)
        return result
    
    def _process_offline_video(self, task: OfflineTask, model_manager) -> Dict:
        """Process offline video task"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "video", "video": task.file_path},
                    {"type": "text", "text": "Analyze this video for medical triage assessment."}
                ]
            }
        ]
        
        result = model_manager.chat_video(messages)
        return result
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get counts by status
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN processed = FALSE THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN processed = TRUE AND synced = FALSE THEN 1 ELSE 0 END) as processed_unsynced,
                SUM(CASE WHEN synced = TRUE THEN 1 ELSE 0 END) as synced
            FROM offline_tasks
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            "total_tasks": stats[0],
            "pending_tasks": stats[1],
            "processed_unsynced": stats[2],
            "synced_tasks": stats[3],
            "storage_path": str(self.base_dir)
        }

# Global instance
offline_storage = OfflineStorageManager() 
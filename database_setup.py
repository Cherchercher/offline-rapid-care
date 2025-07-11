#!/usr/bin/env python3
"""
Database setup for RapidCare
Handles both PostgreSQL (online) and SQLite (offline) databases
"""

import os
import sqlite3
import psycopg
from psycopg.rows import dict_row
import json
from datetime import datetime, timezone
import uuid
from typing import Dict, List, Optional, Any
import logging
import threading
import time
from prompts import CHARACTERISTIC_EXTRACTION_PROMPT

# Import vector search (optional)
try:
    from vector_search import get_vector_search_manager
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages both online (PostgreSQL) and offline (SQLite) databases"""
    
    def __init__(self, 
                 pg_config: Optional[Dict] = None,
                 sqlite_path: str = "rapidcare_offline.db",
                 sync_enabled: bool = True):
        
        self.pg_config = pg_config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'rapidcare'),
            'user': os.getenv('DB_USER', 'rapidcare_user'),
            'password': os.getenv('DB_PASSWORD', 'rapidcare_pass')
        }
        
        self.sqlite_path = sqlite_path
        self.sync_enabled = sync_enabled
        self.online_available = False
        
        # Initialize vector search if available
        self.vector_search = None
        if VECTOR_SEARCH_AVAILABLE:
            try:
                self.vector_search = get_vector_search_manager()
                logger.info("✅ Vector search initialized")
            except Exception as e:
                logger.warning(f"⚠️  Vector search not available: {e}")
                self.vector_search = None
        
        # Initialize databases
        self._init_sqlite()
        self._check_postgresql()
    
    def _init_sqlite(self):
        """Initialize SQLite database for offline use"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Create tables
            self._create_sqlite_tables(cursor)
            
            conn.commit()
            conn.close()
            logger.info("✅ SQLite database initialized")
            
        except Exception as e:
            logger.error(f"❌ SQLite initialization failed: {e}")
            raise
    
    def _create_sqlite_tables(self, cursor):
        """Create SQLite tables"""
        
        # Patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                rfid TEXT,
                name TEXT,
                age INTEGER,
                triage_level TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                location TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sync_status TEXT DEFAULT 'synced',
                sync_timestamp TEXT,
                video_analysis TEXT
            )
        """)
        
        # SOAP Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soap_notes (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                subjective TEXT,
                objective TEXT,
                assessment TEXT,
                plan TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sync_status TEXT DEFAULT 'synced',
                sync_timestamp TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        """)
        
        # Incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT,
                severity TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sync_status TEXT DEFAULT 'synced',
                sync_timestamp TEXT
            )
        """)
        
        # Interactions table (chat logs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_message TEXT NOT NULL,
                patient_id TEXT,
                timestamp TEXT NOT NULL,
                sync_status TEXT DEFAULT 'synced',
                sync_timestamp TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        """)
        
        # Video analyses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_analyses (
                id TEXT PRIMARY KEY,
                video_path TEXT NOT NULL,
                analysis_data TEXT NOT NULL,
                triage_level TEXT,
                role TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sync_status TEXT DEFAULT 'synced',
                sync_timestamp TEXT
            )
        """)
        
        # Missing persons table for reunification
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missing_persons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                description TEXT,
                image_path TEXT,
                contact_info TEXT,
                reported_by TEXT NOT NULL,
                status TEXT DEFAULT 'missing',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sync_status TEXT DEFAULT 'synced',
                sync_timestamp TEXT
            )
        """)
        
        # Sync queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # Vitals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vitals (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                heart_rate INTEGER,
                bp_sys INTEGER,
                bp_dia INTEGER,
                resp_rate INTEGER,
                o2_sat REAL,
                temperature REAL,
                pain_score INTEGER,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_sync_status ON patients(sync_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_soap_notes_patient_id ON soap_notes(patient_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_soap_notes_doctor_id ON soap_notes(doctor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_queue_timestamp ON sync_queue(timestamp)")
    
    def _check_postgresql(self):
        """Check PostgreSQL connection"""
        try:
            conn = psycopg.connect(**self.pg_config, row_factory=dict_row)
            conn.close()
            self.online_available = True
            logger.info("✅ PostgreSQL connection successful")
        except Exception as e:
            logger.warning(f"⚠️  PostgreSQL not available: {e}")
            self.online_available = False
    
    def _create_postgresql_tables(self):
        """Create PostgreSQL tables"""
        try:
            conn = psycopg.connect(**self.pg_config, row_factory=dict_row)
            cursor = conn.cursor()
            
            # Patients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id VARCHAR(255) PRIMARY KEY,
                    rfid VARCHAR(255),
                    name VARCHAR(255),
                    age INTEGER,
                    triage_level VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    notes TEXT,
                    location VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    video_analysis JSONB
                )
            """)
            
            # SOAP Notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS soap_notes (
                    id VARCHAR(255) PRIMARY KEY,
                    patient_id VARCHAR(255) NOT NULL,
                    doctor_id VARCHAR(255) NOT NULL,
                    subjective TEXT,
                    objective TEXT,
                    assessment TEXT,
                    plan TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                )
            """)
            
            # Incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    location VARCHAR(255),
                    severity VARCHAR(50),
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            # Interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id VARCHAR(255) PRIMARY KEY,
                    role VARCHAR(100) NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    patient_id VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    model_mode VARCHAR(50),
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                )
            """)
            
            # Video analyses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_analyses (
                    id VARCHAR(255) PRIMARY KEY,
                    video_path TEXT NOT NULL,
                    analysis_data JSONB NOT NULL,
                    triage_level VARCHAR(50),
                    role VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            # Missing persons table for reunification
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS missing_persons (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    age INTEGER,
                    description TEXT,
                    image_path TEXT,
                    contact_info TEXT,
                    reported_by VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'missing',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            # Vitals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vitals (
                    id VARCHAR(255) PRIMARY KEY,
                    patient_id VARCHAR(255) NOT NULL,
                    heart_rate INTEGER,
                    bp_sys INTEGER,
                    bp_dia INTEGER,
                    resp_rate INTEGER,
                    o2_sat REAL,
                    temperature REAL,
                    pain_score INTEGER,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_by VARCHAR(255),
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ PostgreSQL tables created")
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL table creation failed: {e}")
            raise
    
    def get_sqlite_connection(self):
        """Get SQLite connection"""
        return sqlite3.connect(self.sqlite_path)
    
    def get_postgresql_connection(self):
        """Get PostgreSQL connection"""
        if not self.online_available:
            raise Exception("PostgreSQL not available")
        return psycopg.connect(**self.pg_config, row_factory=dict_row)
    
    def add_patient(self, patient_data: Dict) -> str:
        """Add a new patient to the database"""
        patient_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Generate RFID if not provided
        rfid = patient_data.get('rfid', f"RFID-{patient_id[:8].upper()}")
        
        patient_record = {
            'id': patient_id,
            'rfid': rfid,
            'name': patient_data.get('name', 'Unknown'),
            'age': patient_data.get('age'),
            'triage_level': patient_data.get('triage_level', 'Green'),
            'status': patient_data.get('status', 'Active'),
            'notes': patient_data.get('notes', ''),
            'location': patient_data.get('location', 'Unknown'),
            'created_at': timestamp,
            'updated_at': timestamp,
            'sync_status': 'pending',
            'video_analysis': json.dumps(patient_data.get('video_analysis'))
        }
        
        # Add to SQLite (always available)
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO patients 
                (id, rfid, name, age, triage_level, status, notes, location, created_at, updated_at, sync_status, video_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_record['id'],
                patient_record['rfid'],
                patient_record['name'],
                patient_record['age'],
                patient_record['triage_level'],
                patient_record['status'],
                patient_record['notes'],
                patient_record['location'],
                patient_record['created_at'],
                patient_record['updated_at'],
                patient_record['sync_status'],
                patient_record['video_analysis']
            ))
            
            conn.commit()
            conn.close()
            
            # Add to sync queue
            self._add_to_sync_queue('patients', patient_id, 'INSERT', patient_record)
            
            # Index for vector search if available
            if self.vector_search and self.vector_search.is_available():
                try:
                    self.vector_search.index_patient(patient_record)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to index patient for search: {e}")
            
            logger.info(f"✅ Patient {patient_id} added to offline database")
            
        except Exception as e:
            logger.error(f"❌ Failed to add patient to SQLite: {e}")
            raise
        
        # Try to sync to PostgreSQL if available
        if self.online_available and self.sync_enabled:
            self._sync_to_postgresql('patients', patient_record, 'INSERT')
        
        return patient_id
    
    def get_patients(self, limit: int = 100) -> List[Dict]:
        """Get patients from database"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM patients 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            patients = []
            for row in rows:
                patient = dict(zip(columns, row))
                if patient.get('video_analysis'):
                    patient['video_analysis'] = json.loads(patient['video_analysis'])
                patients.append(patient)
            
            conn.close()
            return patients
            
        except Exception as e:
            logger.error(f"❌ Failed to get patients: {e}")
            return []
    
    def add_soap_note(self, soap_data: Dict) -> str:
        """Add SOAP note for a patient"""
        soap_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        soap_record = {
            'id': soap_id,
            'patient_id': soap_data.get('patient_id'),
            'doctor_id': soap_data.get('doctor_id'),
            'subjective': soap_data.get('subjective', ''),
            'objective': soap_data.get('objective', ''),
            'assessment': soap_data.get('assessment', ''),
            'plan': soap_data.get('plan', ''),
            'created_at': timestamp,
            'updated_at': timestamp,
            'sync_status': 'pending'
        }
        
        # Add to SQLite
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO soap_notes 
                (id, patient_id, doctor_id, subjective, objective, assessment, plan, created_at, updated_at, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                soap_record['id'],
                soap_record['patient_id'],
                soap_record['doctor_id'],
                soap_record['subjective'],
                soap_record['objective'],
                soap_record['assessment'],
                soap_record['plan'],
                soap_record['created_at'],
                soap_record['updated_at'],
                soap_record['sync_status']
            ))
            
            conn.commit()
            conn.close()
            
            # Add to sync queue
            self._add_to_sync_queue('soap_notes', soap_id, 'INSERT', soap_record)
            
            # Index for vector search if available
            if self.vector_search and self.vector_search.is_available():
                try:
                    self.vector_search.index_soap_note(soap_record)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to index SOAP note for search: {e}")
            
            logger.info(f"✅ SOAP note {soap_id} added for patient {soap_data.get('patient_id')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to add SOAP note: {e}")
            raise
        
        # Try to sync to PostgreSQL if available
        if self.online_available and self.sync_enabled:
            self._sync_to_postgresql('soap_notes', soap_record, 'INSERT')
        
        return soap_id
    
    def get_soap_notes(self, patient_id: str = None, doctor_id: str = None) -> List[Dict]:
        """Get SOAP notes from database"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            if patient_id:
                cursor.execute("""
                    SELECT * FROM soap_notes 
                    WHERE patient_id = ?
                    ORDER BY created_at DESC
                """, (patient_id,))
            elif doctor_id:
                cursor.execute("""
                    SELECT * FROM soap_notes 
                    WHERE doctor_id = ?
                    ORDER BY created_at DESC
                """, (doctor_id,))
            else:
                cursor.execute("""
                    SELECT * FROM soap_notes 
                    ORDER BY created_at DESC
                """)
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            soap_notes = []
            for row in rows:
                soap_note = dict(zip(columns, row))
                soap_notes.append(soap_note)
            
            conn.close()
            return soap_notes
            
        except Exception as e:
            logger.error(f"❌ Failed to get SOAP notes: {e}")
            return []
    
    def update_soap_note(self, soap_id: str, soap_data: Dict) -> bool:
        """Update SOAP note"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE soap_notes 
                SET subjective = ?, objective = ?, assessment = ?, plan = ?, updated_at = ?, sync_status = ?
                WHERE id = ?
            """, (
                soap_data.get('subjective', ''),
                soap_data.get('objective', ''),
                soap_data.get('assessment', ''),
                soap_data.get('plan', ''),
                timestamp,
                'pending',
                soap_id
            ))
            
            conn.commit()
            conn.close()
            
            # Add to sync queue
            self._add_to_sync_queue('soap_notes', soap_id, 'UPDATE', soap_data)
            
            logger.info(f"✅ SOAP note {soap_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update SOAP note: {e}")
            return False
    
    def log_interaction(self, interaction_data: Dict) -> str:
        """Log an interaction (chat message)"""
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        interaction_record = {
            'id': interaction_id,
            'role': interaction_data.get('role', 'PARAMEDIC'),
            'user_message': interaction_data.get('user_message', ''),
            'assistant_message': interaction_data.get('assistant_message', ''),
            'patient_id': interaction_data.get('patient_id'),
            'timestamp': timestamp,
            'sync_status': 'pending',
            'model_mode': interaction_data.get('model_mode', 'unknown')
        }
        
        # Add to SQLite
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO interactions 
                (id, role, user_message, assistant_message, patient_id, timestamp, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction_record['id'],
                interaction_record['role'],
                interaction_record['user_message'],
                interaction_record['assistant_message'],
                interaction_record['patient_id'],
                interaction_record['timestamp'],
                interaction_record['sync_status']
            ))
            
            conn.commit()
            conn.close()
            
            # Add to sync queue
            self._add_to_sync_queue('interactions', interaction_id, 'INSERT', interaction_record)
            
        except Exception as e:
            logger.error(f"❌ Failed to log interaction: {e}")
            raise
        
        # Try to sync to PostgreSQL if available
        if self.online_available and self.sync_enabled:
            self._sync_to_postgresql('interactions', interaction_record, 'INSERT')
        
        return interaction_id
    
    def save_video_analysis(self, analysis_data: Dict) -> str:
        """Save video analysis to database"""
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO video_analyses 
                (id, video_path, analysis_data, triage_level, role, timestamp, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                analysis_data.get('video_path', ''),
                json.dumps(analysis_data.get('analysis', {})),
                analysis_data.get('triage_level', ''),
                analysis_data.get('role', ''),
                timestamp,
                'pending'
            ))
            
            conn.commit()
            conn.close()
            
            # Add to sync queue
            self._add_to_sync_queue('video_analyses', analysis_id, 'INSERT', analysis_data)
            
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error saving video analysis: {e}")
            raise
    
    def add_missing_person(self, person_data: Dict) -> str:
        """Add a missing person to the database"""
        person_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO missing_persons 
                (id, name, age, description, image_path, contact_info, reported_by, status, created_at, updated_at, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                person_data.get('name', ''),
                person_data.get('age'),
                person_data.get('description', ''),
                person_data.get('image_path', ''),
                person_data.get('contact_info', ''),
                person_data.get('reported_by', ''),
                person_data.get('status', 'missing'),
                timestamp,
                timestamp,
                'pending'
            ))
            
            conn.commit()
            conn.close()
            
            # Add to sync queue
            self._add_to_sync_queue('missing_persons', person_id, 'INSERT', person_data)
            
            # Index for vector search if available
            if self.vector_search and self.vector_search.is_available():
                try:
                    self.vector_search.index_missing_person(person_data)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to index missing person for search: {e}")
            
            logger.info(f"✅ Missing person {person_id} added to offline database")
            return person_id
            
        except Exception as e:
            logger.error(f"Error adding missing person: {e}")
            raise
    
    def get_missing_persons(self, limit: int = 100) -> List[Dict]:
        """Get all missing persons from database"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM missing_persons 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting missing persons: {e}")
            return []
    
    def find_missing_person_match(self, image_path: str, threshold: float = 0.7) -> List[Dict]:
        """Find potential matches for a missing person using image similarity"""
        try:
            # Get all missing persons with images
            missing_persons = self.get_missing_persons()
            matches = []
            
            for person in missing_persons:
                if person.get('image_path'):
                    # Use Gemma 3n to compare images
                    similarity_score = self._compare_images(image_path, person['image_path'])
                    
                    if similarity_score >= threshold:
                        person['similarity_score'] = similarity_score
                        matches.append(person)
            
            # Sort by similarity score (highest first)
            matches.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding missing person match: {e}")
            return []
    
    def _compare_images(self, image1_path: str, image2_path: str) -> float:
        """Compare two images using Gemma 3n for similarity"""
        try:
            # Use the model manager to analyze both images and compare descriptions
            from model_manager import get_model_manager
            model_manager = get_model_manager()
            
            # Generate structured descriptions for both images
            prompt = CHARACTERISTIC_EXTRACTION_PROMPT
            
            # Create image URLs (use uploads server port)
            image1_url = f"http://127.0.0.1:11435/{image1_path}"
            image2_url = f"http://127.0.0.1:11435/{image2_path}"
            
            # Get descriptions
            desc1 = model_manager.analyze_image_with_url(image1_url, prompt)
            desc2 = model_manager.analyze_image_with_url(image2_url, prompt)
            
            if desc1['success'] and desc2['success']:
                # Calculate similarity based on structured features
                similarity_score = self._calculate_structured_similarity(
                    desc1['response'], desc2['response']
                )
                return similarity_score
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error comparing images: {e}")
            return 0.0
    
    def _calculate_structured_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between two structured descriptions"""
        try:
            # Parse structured descriptions
            features1 = self._parse_structured_description(desc1)
            features2 = self._parse_structured_description(desc2)
            
            if not features1 or not features2:
                return 0.0
            
            # Calculate weighted similarity scores
            weights = {
                'face_shape': 0.15,
                'hair_color': 0.12,
                'hair_length': 0.08,
                'eye_color': 0.12,
                'skin_tone': 0.10,
                'height': 0.08,
                'build': 0.08,
                'clothing_top': 0.07,
                'clothing_bottom': 0.07,
                'accessories': 0.05,
                'distinctive': 0.08
            }
            
            total_score = 0.0
            total_weight = 0.0
            
            for feature, weight in weights.items():
                if feature in features1 and feature in features2:
                    feature_score = self._compare_feature(
                        features1[feature], features2[feature]
                    )
                    total_score += feature_score * weight
                    total_weight += weight
            
            if total_weight > 0:
                return total_score / total_weight
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating structured similarity: {e}")
            return 0.0
    
    def _parse_structured_description(self, description: str) -> dict:
        """Parse structured description into feature dictionary"""
        features = {}
        
        try:
            lines = description.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if '**Physical Features:**' in line:
                    current_section = 'physical'
                elif '**Clothing:**' in line:
                    current_section = 'clothing'
                elif '**Distinctive Features:**' in line:
                    current_section = 'distinctive'
                elif '**Age Range:**' in line:
                    current_section = 'age'
                elif line.startswith('-') and current_section:
                    # Parse feature
                    feature_text = line[1:].strip()
                    if ':' in feature_text:
                        key, value = feature_text.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        
                        if current_section == 'physical':
                            if 'face' in key:
                                features['face_shape'] = value
                            elif 'hair' in key:
                                if 'color' in key:
                                    features['hair_color'] = value
                                elif 'length' in key:
                                    features['hair_length'] = value
                            elif 'eyes' in key:
                                features['eye_color'] = value
                            elif 'skin' in key:
                                features['skin_tone'] = value
                            elif 'height' in key:
                                features['height'] = value
                            elif 'build' in key:
                                features['build'] = value
                        elif current_section == 'clothing':
                            if 'top' in key:
                                features['clothing_top'] = value
                            elif 'bottom' in key:
                                features['clothing_bottom'] = value
                            elif 'accessories' in key:
                                features['accessories'] = value
                        elif current_section == 'distinctive':
                            features['distinctive'] = value
            
            return features
            
        except Exception as e:
            logger.error(f"Error parsing structured description: {e}")
            return {}
    
    def _compare_feature(self, value1: str, value2: str) -> float:
        """Compare two feature values and return similarity score"""
        if not value1 or not value2:
            return 0.0
        
        # Normalize values
        v1 = value1.lower().strip()
        v2 = value2.lower().strip()
        
        # Exact match
        if v1 == v2:
            return 1.0
        
        # Partial match (one contains the other)
        if v1 in v2 or v2 in v1:
            return 0.8
        
        # Word overlap
        words1 = set(v1.split())
        words2 = set(v2.split())
        
        if len(words1) > 0 and len(words2) > 0:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            if len(union) > 0:
                return len(intersection) / len(union)
        
        return 0.0
    
    def _add_to_sync_queue(self, table_name: str, record_id: str, operation: str, data: Dict):
        """Add operation to sync queue"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sync_queue 
                (id, table_name, record_id, operation, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                table_name,
                record_id,
                operation,
                json.dumps(data),
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to add to sync queue: {e}")
    
    def _sync_to_postgresql(self, table_name: str, data: Dict, operation: str):
        """Sync data to PostgreSQL"""
        if not self.online_available:
            return
        
        try:
            conn = self.get_postgresql_connection()
            
            if operation == 'INSERT':
                if table_name == 'patients':
                    conn.execute("""
                        INSERT INTO patients 
                        (id, rfid, name, age, triage_level, status, notes, location, created_at, updated_at, video_analysis)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                        rfid = EXCLUDED.rfid,
                        name = EXCLUDED.name,
                        age = EXCLUDED.age,
                        triage_level = EXCLUDED.triage_level,
                        status = EXCLUDED.status,
                        notes = EXCLUDED.notes,
                        location = EXCLUDED.location,
                        updated_at = EXCLUDED.updated_at,
                        video_analysis = EXCLUDED.video_analysis
                    """, (
                        data['id'],
                        data['rfid'],
                        data['name'],
                        data['age'],
                        data['triage_level'],
                        data['status'],
                        data['notes'],
                        data['location'],
                        data['created_at'],
                        data['updated_at'],
                        data.get('video_analysis')
                    ))
                
                elif table_name == 'soap_notes':
                    conn.execute("""
                        INSERT INTO soap_notes 
                        (id, patient_id, doctor_id, subjective, objective, assessment, plan, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                        subjective = EXCLUDED.subjective,
                        objective = EXCLUDED.objective,
                        assessment = EXCLUDED.assessment,
                        plan = EXCLUDED.plan,
                        updated_at = EXCLUDED.updated_at
                    """, (
                        data['id'],
                        data['patient_id'],
                        data['doctor_id'],
                        data['subjective'],
                        data['objective'],
                        data['assessment'],
                        data['plan'],
                        data['created_at'],
                        data['updated_at']
                    ))
                
                elif table_name == 'interactions':
                    conn.execute("""
                        INSERT INTO interactions 
                        (id, role, user_message, assistant_message, patient_id, timestamp, model_mode)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        data['id'],
                        data['role'],
                        data['user_message'],
                        data['assistant_message'],
                        data['patient_id'],
                        data['timestamp'],
                        data.get('model_mode')
                    ))
                
                elif table_name == 'video_analyses':
                    conn.execute("""
                        INSERT INTO video_analyses 
                        (id, video_path, analysis_data, triage_level, role, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        data['id'],
                        data['video_path'],
                        data['analysis_data'],
                        data['triage_level'],
                        data['role'],
                        data['timestamp']
                    ))
                
                elif table_name == 'vitals':
                    conn.execute("""
                        INSERT INTO vitals 
                        (id, patient_id, heart_rate, bp_sys, bp_dia, resp_rate, o2_sat, temperature, pain_score, timestamp, created_at, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        data['id'],
                        data['patient_id'],
                        data['heart_rate'],
                        data['bp_sys'],
                        data['bp_dia'],
                        data['resp_rate'],
                        data['o2_sat'],
                        data['temperature'],
                        data['pain_score'],
                        data['timestamp'],
                        data['created_at'],
                        data['created_by']
                    ))
            
            conn.close()
            
            # Mark as synced in SQLite
            self._mark_synced(table_name, data['id'])
            
            logger.info(f"✅ Synced {operation} on {table_name} to PostgreSQL")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync to PostgreSQL: {e}")
    
    def _mark_synced(self, table_name: str, record_id: str):
        """Mark record as synced in SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE {table_name} 
                SET sync_status = 'synced', sync_timestamp = ? 
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), record_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to mark as synced: {e}")
    
    def sync_pending_changes(self):
        """Sync all pending changes to PostgreSQL"""
        if not self.online_available:
            logger.warning("⚠️  PostgreSQL not available, skipping sync")
            return
        
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            # Get pending sync queue items
            cursor.execute("""
                SELECT * FROM sync_queue 
                ORDER BY timestamp ASC
            """)
            
            queue_items = cursor.fetchall()
            conn.close()
            
            if not queue_items:
                logger.info("✅ No pending changes to sync")
                return
            
            logger.info(f"🔄 Syncing {len(queue_items)} pending changes...")
            
            for item in queue_items:
                try:
                    data = json.loads(item[4])  # data column
                    self._sync_to_postgresql(item[1], data, item[3])  # table_name, data, operation
                    
                    # Remove from sync queue
                    self._remove_from_sync_queue(item[0])  # id
                    
                except Exception as e:
                    logger.error(f"❌ Failed to sync item {item[0]}: {e}")
                    # Increment retry count
                    self._increment_retry_count(item[0])
            
            logger.info("✅ Sync completed")
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
    
    def _remove_from_sync_queue(self, queue_id: str):
        """Remove item from sync queue"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM sync_queue WHERE id = ?", (queue_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to remove from sync queue: {e}")
    
    def _increment_retry_count(self, queue_id: str):
        """Increment retry count for failed sync item"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sync_queue 
                SET retry_count = retry_count + 1 
                WHERE id = ?
            """, (queue_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to increment retry count: {e}")
    
    def get_sync_status(self) -> Dict:
        """Get sync status information"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            
            # Count pending items
            cursor.execute("SELECT COUNT(*) FROM sync_queue")
            pending_count = cursor.fetchone()[0]
            
            # Count unsynced records by table
            cursor.execute("""
                SELECT table_name, COUNT(*) 
                FROM sync_queue 
                GROUP BY table_name
            """)
            table_counts = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'online_available': self.online_available,
                'sync_enabled': self.sync_enabled,
                'pending_changes': pending_count,
                'table_counts': table_counts,
                'last_sync_attempt': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get sync status: {e}")
            return {
                'online_available': self.online_available,
                'sync_enabled': self.sync_enabled,
                'error': str(e)
            }

    def add_vitals(self, vitals_data: Dict) -> str:
        """Add a new vitals record for a patient"""
        vitals_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            'id': vitals_id,
            'patient_id': vitals_data['patient_id'],
            'heart_rate': vitals_data.get('heart_rate'),
            'bp_sys': vitals_data.get('bp_sys'),
            'bp_dia': vitals_data.get('bp_dia'),
            'resp_rate': vitals_data.get('resp_rate'),
            'o2_sat': vitals_data.get('o2_sat'),
            'temperature': vitals_data.get('temperature'),
            'pain_score': vitals_data.get('pain_score'),
            'timestamp': vitals_data.get('timestamp', now),
            'created_at': now,
            'created_by': vitals_data.get('created_by', 'PARAMEDIC')
        }
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vitals (id, patient_id, heart_rate, bp_sys, bp_dia, resp_rate, o2_sat, temperature, pain_score, timestamp, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['id'], record['patient_id'], record['heart_rate'], record['bp_sys'], record['bp_dia'],
                record['resp_rate'], record['o2_sat'], record['temperature'], record['pain_score'],
                record['timestamp'], record['created_at'], record['created_by']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to add vitals: {e}")
            raise
        # Optionally sync to PostgreSQL if online
        if self.online_available and self.sync_enabled:
            self._sync_to_postgresql('vitals', record, 'INSERT')
        return vitals_id
    def get_vitals(self, patient_id: str) -> List[Dict]:
        """Get all vitals for a patient, ordered by timestamp desc"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM vitals WHERE patient_id = ? ORDER BY timestamp DESC
            """, (patient_id,))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            vitals = [dict(zip(columns, row)) for row in rows]
            conn.close()
            return vitals
        except Exception as e:
            logger.error(f"❌ Failed to get vitals: {e}")
            return []

# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

if __name__ == "__main__":
    # Test database setup
    print("🚑 Testing Database Setup")
    print("=" * 50)
    
    try:
        db = get_db_manager()
        print("✅ Database manager initialized")
        
        # Test adding a patient
        patient_data = {
            'triage': 'Red',
            'status': 'Active',
            'notes': 'Test patient',
            'location': 'Zone A'
        }
        
        patient_id = db.add_patient(patient_data)
        print(f"✅ Patient added: {patient_id}")
        
        # Test getting patients
        patients = db.get_patients()
        print(f"✅ Retrieved {len(patients)} patients")
        
        # Test adding a SOAP note
        soap_data = {
            'patient_id': patient_id,
            'doctor_id': 'Dr. Smith',
            'subjective': 'Patient reported chest pain',
            'objective': 'Heart rate: 100 bpm',
            'assessment': 'Possible myocardial infarction',
            'plan': 'Administer nitroglycerin'
        }
        
        soap_id = db.add_soap_note(soap_data)
        print(f"✅ SOAP note added: {soap_id}")
        
        # Test getting SOAP notes
        soap_notes = db.get_soap_notes(patient_id=patient_id)
        print(f"✅ Retrieved {len(soap_notes)} SOAP notes")
        
        # Test updating a SOAP note
        updated_soap_data = {
            'subjective': 'Patient reported chest pain',
            'objective': 'Heart rate: 100 bpm',
            'assessment': 'Possible myocardial infarction',
            'plan': 'Administer nitroglycerin'
        }
        
        updated = db.update_soap_note(soap_id, updated_soap_data)
        print(f"✅ SOAP note updated: {updated}")
        
        # Test adding vitals
        vitals_data = {
            'patient_id': patient_id,
            'heart_rate': 80,
            'bp_sys': 120,
            'bp_dia': 80,
            'resp_rate': 18,
            'o2_sat': 98.5,
            'temperature': 36.8,
            'pain_score': 5,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'created_by': 'Dr. Jones'
        }
        vitals_id = db.add_vitals(vitals_data)
        print(f"✅ Vitals added: {vitals_id}")

        # Test getting vitals
        vitals_records = db.get_vitals(patient_id)
        print(f"✅ Retrieved {len(vitals_records)} vitals records")
        
        # Test sync status
        sync_status = db.get_sync_status()
        print(f"✅ Sync status: {sync_status}")
        
        print("\n🎉 Database setup test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup test failed: {e}")
        import traceback
        traceback.print_exc() 
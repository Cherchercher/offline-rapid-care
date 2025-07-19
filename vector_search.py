#!/usr/bin/env python3
"""
Vector Search Integration for RapidCare
Provides AI-powered semantic search across medical data
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
import numpy as np

# Vector database - using Chroma for simplicity and offline capability
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("⚠️  ChromaDB not available. Install with: pip install chromadb")

# Embedding model for text
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    print("⚠️  SentenceTransformers not available. Install with: pip install sentence-transformers")

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result with metadata"""
    id: str
    content: str
    metadata: Dict
    similarity_score: float
    source_type: str  # 'patient', 'soap_note', 'video_analysis', etc.

class VectorSearchManager:
    """Manages vector search capabilities for medical data"""
    
    def __init__(self, 
                 db_path: str = "./vector_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 collection_name: str = "medical_data"):
        
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        
        # Initialize components
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize ChromaDB and embedding model"""
        if not CHROMA_AVAILABLE:
            logger.warning("ChromaDB not available - vector search disabled")
            return
        
        if not EMBEDDING_AVAILABLE:
            logger.warning("SentenceTransformers not available - vector search disabled")
            return
        
        try:
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Medical emergency response data"}
            )
            
            # Load embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            logger.info(f"✅ Vector search initialized with {self.embedding_model_name}")
            
        except Exception as e:
            logger.error(f"❌ Vector search initialization failed: {e}")
            self.chroma_client = None
            self.collection = None
            self.embedding_model = None
    
    def is_available(self) -> bool:
        """Check if vector search is available"""
        return (self.chroma_client is not None and 
                self.collection is not None and 
                self.embedding_model is not None)
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding for text"""
        if not self.is_available():
            return []
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Embedding creation failed: {e}")
            return []
    
    def _create_searchable_content(self, data: Dict, data_type: str) -> str:
        """Create searchable text content from data"""
        if data_type == "patient":
            return f"""
            Patient: {data.get('name', 'Unknown')}
            Age: {data.get('age', 'Unknown')}
            Triage Level: {data.get('triage_level', 'Unknown')}
            Status: {data.get('status', 'Unknown')}
            Location: {data.get('location', 'Unknown')}
            Notes: {data.get('notes', '')}
            RFID: {data.get('rfid', 'Unknown')}
            """.strip()
        
        elif data_type == "missing_person":
            # Enhanced missing person content with characteristics
            characteristics = data.get('characteristics', {})
            physical = characteristics.get('physical_features', {})
            clothing = characteristics.get('clothing', {})
            distinctive = characteristics.get('distinctive_features', [])
            
            return f"""
            Missing Person: {data.get('name', 'Unknown')}
            Gender: {physical.get('gender', 'Unknown')} | Age: {data.get('age', 'Unknown')} | Age Range: {characteristics.get('age_range', 'Unknown')}
            Physical Features: Face shape {physical.get('face_shape', 'Unknown')}, Hair {physical.get('hair_color', 'Unknown')} {physical.get('hair_length', '')}, Eyes {physical.get('eye_color', 'Unknown')}, Skin {physical.get('skin_tone', 'Unknown')}, Height {physical.get('height', 'Unknown')}, Build {physical.get('build', 'Unknown')}
            Clothing: Top {clothing.get('top', 'Unknown')}, Bottom {clothing.get('bottom', 'Unknown')}, Accessories {clothing.get('accessories', 'None')}
            Distinctive Features: {', '.join(distinctive) if distinctive else 'None'}
            Description: {data.get('description', '')}
            Contact Info: {data.get('contact_info', '')}
            Reported By: {data.get('reported_by', 'Unknown')}
            Status: {data.get('status', 'missing')}
            """.strip()
        
        elif data_type == "soap_note":
            return f"""
            SOAP Note for Patient {data.get('patient_id', 'Unknown')}
            Subjective: {data.get('subjective', '')}
            Objective: {data.get('objective', '')}
            Assessment: {data.get('assessment', '')}
            Plan: {data.get('plan', '')}
            """.strip()
        
        elif data_type == "video_analysis":
            return f"""
            Video Analysis
            Triage Level: {data.get('triage_level', 'Unknown')}
            Analysis: {data.get('analysis', '')}
            Role: {data.get('role', 'Unknown')}
            """.strip()
        
        elif data_type == "vitals":
            return f"""
            Vitals for Patient {data.get('patient_id', 'Unknown')}
            Heart Rate: {data.get('heart_rate', 'Unknown')} BPM
            Blood Pressure: {data.get('bp_sys', 'Unknown')}/{data.get('bp_dia', 'Unknown')} mmHg
            Respiratory Rate: {data.get('resp_rate', 'Unknown')}
            O2 Saturation: {data.get('o2_sat', 'Unknown')}%
            Temperature: {data.get('temperature', 'Unknown')}°F
            Pain Score: {data.get('pain_score', 'Unknown')}/10
            """.strip()
        
        else:
            return json.dumps(data, indent=2)
    
    def index_patient(self, patient_data: Dict) -> bool:
        """Index a patient record for search"""
        if not self.is_available():
            return False
        
        try:
            patient_id = patient_data.get('id', str(uuid.uuid4()))
            content = self._create_searchable_content(patient_data, "patient")
            embedding = self._create_embedding(content)
            
            if not embedding:
                return False
            
            # Prepare metadata and sanitize values
            metadata = {
                'id': patient_id,
                'type': 'patient',
                'name': patient_data.get('name', ''),
                'age': patient_data.get('age', ''),
                'triage_level': patient_data.get('triage_level', ''),
                'location': patient_data.get('location', ''),
                'created_at': patient_data.get('created_at', '')
            }
            
            # Sanitize metadata to ensure all values are strings
            sanitized_metadata = self._sanitize_metadata(metadata)
            
            # Add to vector database
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[sanitized_metadata],
                ids=[f"patient_{patient_id}"]
            )
            
            logger.info(f"✅ Indexed patient {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index patient: {e}")
            return False
    
    def index_soap_note(self, soap_data: Dict) -> bool:
        """Index a SOAP note for search"""
        if not self.is_available():
            return False
        
        try:
            soap_id = soap_data.get('id', str(uuid.uuid4()))
            content = self._create_searchable_content(soap_data, "soap_note")
            embedding = self._create_embedding(content)
            
            if not embedding:
                return False
            
            # Prepare metadata and sanitize values
            metadata = {
                'id': soap_id,
                'type': 'soap_note',
                'patient_id': soap_data.get('patient_id', ''),
                'doctor_id': soap_data.get('doctor_id', ''),
                'created_at': soap_data.get('created_at', '')
            }
            
            # Sanitize metadata to ensure all values are strings
            sanitized_metadata = self._sanitize_metadata(metadata)
            
            # Add to vector database
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[sanitized_metadata],
                ids=[f"soap_{soap_id}"]
            )
            
            logger.info(f"✅ Indexed SOAP note {soap_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index SOAP note: {e}")
            return False
    
    def index_video_analysis(self, analysis_data: Dict) -> bool:
        """Index a video analysis for search"""
        if not self.is_available():
            return False
        
        try:
            analysis_id = analysis_data.get('id', str(uuid.uuid4()))
            content = self._create_searchable_content(analysis_data, "video_analysis")
            embedding = self._create_embedding(content)
            
            if not embedding:
                return False
            
            # Prepare metadata and sanitize values
            metadata = {
                'id': analysis_id,
                'type': 'video_analysis',
                'triage_level': analysis_data.get('triage_level', ''),
                'role': analysis_data.get('role', ''),
                'timestamp': analysis_data.get('timestamp', '')
            }
            
            # Sanitize metadata to ensure all values are strings
            sanitized_metadata = self._sanitize_metadata(metadata)
            
            # Add to vector database
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[sanitized_metadata],
                ids=[f"video_{analysis_id}"]
            )
            
            logger.info(f"✅ Indexed video analysis {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index video analysis: {e}")
            return False

    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Convert all metadata values to strings to avoid ChromaDB errors"""
        sanitized = {}
        for key, value in metadata.items():
            if value is None:
                sanitized[key] = ''
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = str(value)
            else:
                sanitized[key] = str(value) if value else ''
        return sanitized

    def index_missing_person(self, person_data: Dict) -> bool:
        """Index a missing person record for search"""
        if not self.is_available():
            return False
        
        try:
            person_id = person_data.get('id', str(uuid.uuid4()))
            content = self._create_searchable_content(person_data, "missing_person")
            embedding = self._create_embedding(content)
            
            if not embedding:
                return False
            
            # Prepare metadata and sanitize values
            metadata = {
                'id': person_id,
                'type': 'missing_person',
                'name': person_data.get('name', ''),
                'age': person_data.get('age', ''),
                'status': person_data.get('status', 'missing'),
                'reported_by': person_data.get('reported_by', ''),
                'created_at': person_data.get('created_at', ''),
                'image_path': person_data.get('image_path', ''),
                'contact_info': person_data.get('contact_info', ''),
                'characteristics': json.dumps(person_data.get('characteristics', {}))
            }
            
            # Sanitize metadata to ensure all values are strings
            sanitized_metadata = self._sanitize_metadata(metadata)
            
            # Add to vector database
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[sanitized_metadata],
                ids=[f"missing_{person_id}"]
            )
            
            logger.info(f"✅ Indexed missing person {person_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index missing person: {e}")
            return False
    
    def search_similar_cases(self, 
                           query: str, 
                           limit: int = 10,
                           filters: Optional[Dict] = None) -> List[SearchResult]:
        """Search for similar medical cases"""
        if not self.is_available():
            return []
        
        try:
            # Create query embedding
            query_embedding = self._create_embedding(query)
            if not query_embedding:
                return []
            
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if value:
                        where_clause[key] = value
            
            # Search vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    search_results.append(SearchResult(
                        id=doc_id,
                        content=results['documents'][0][i],
                        metadata=results['metadatas'][0][i],
                        similarity_score=results['distances'][0][i] if 'distances' in results else 0.0,
                        source_type=results['metadatas'][0][i].get('type', 'unknown')
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def find_similar_patients(self, 
                            patient_data: Dict, 
                            limit: int = 5) -> List[SearchResult]:
        """Find patients with similar conditions"""
        if not self.is_available():
            return []
        
        # Create search query from patient data
        query = self._create_searchable_content(patient_data, "patient")
        
        # Search with patient filter
        return self.search_similar_cases(
            query=query,
            limit=limit,
            filters={'type': 'patient'}
        )
    
    def search_medical_notes(self, 
                           query: str, 
                           limit: int = 10) -> List[SearchResult]:
        """Search across all medical notes"""
        if not self.is_available():
            return []
        
        return self.search_similar_cases(
            query=query,
            limit=limit,
            filters={'type': 'soap_note'}
        )
    
    def search_missing_persons(self, 
                             query: str, 
                             limit: int = 10) -> List[SearchResult]:
        """Search for missing persons"""
        if not self.is_available():
            return []
        
        return self.search_similar_cases(
            query=query,
            limit=limit,
            filters={'type': 'missing_person'}
        )
    
    def find_potential_matches(self, 
                             person_data: Dict, 
                             limit: int = 5) -> List[SearchResult]:
        """Find potential matches for a missing person"""
        if not self.is_available():
            return []
        
        # Create search query from person data
        query = self._create_searchable_content(person_data, "missing_person")
        
        # Search with missing person filter
        return self.search_similar_cases(
            query=query,
            limit=limit,
            filters={'type': 'missing_person'}
        )
    
    def search_patients_for_reunification(self, 
                                        query: str, 
                                        limit: int = 10) -> List[SearchResult]:
        """Search patients for reunification purposes"""
        if not self.is_available():
            return []
        
        return self.search_similar_cases(
            query=query,
            limit=limit,
            filters={'type': 'patient'}
        )
    
    def get_reunification_recommendations(self, 
                                        person_type: str, 
                                        description: str) -> List[SearchResult]:
        """Get reunification recommendations based on person type and description"""
        if not self.is_available():
            return []
        
        query = f"Person Type: {person_type}. Description: {description}. Reunification protocols and procedures."
        
        return self.search_similar_cases(
            query=query,
            limit=5,
            filters={'type': 'soap_note'}
        )
    
    def bulk_index_from_database(self, db_manager) -> int:
        """Bulk index existing data from database"""
        if not self.is_available():
            return 0
        
        indexed_count = 0
        
        try:
            # Index patients
            patients = db_manager.get_patients(limit=1000)
            for patient in patients:
                if self.index_patient(patient):
                    indexed_count += 1
            
            # Index SOAP notes
            for patient in patients:
                soap_notes = db_manager.get_soap_notes(patient_id=patient['id'])
                for soap_note in soap_notes:
                    if self.index_soap_note(soap_note):
                        indexed_count += 1
            
            # Index missing persons
            missing_persons = db_manager.get_missing_persons(limit=1000)
            for person in missing_persons:
                if self.index_missing_person(person):
                    indexed_count += 1
            
            logger.info(f"✅ Bulk indexed {indexed_count} records")
            return indexed_count
            
        except Exception as e:
            logger.error(f"❌ Bulk indexing failed: {e}")
            return indexed_count
    

    
    def clear_index(self) -> bool:
        """Clear all indexed data"""
        if not self.is_available():
            return False
        
        try:
            self.collection.delete()
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Medical emergency response data"}
            )
            logger.info("✅ Index cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear index: {e}")
            return False

# Global instance
_vector_search_manager = None

def get_vector_search_manager() -> VectorSearchManager:
    """Get global vector search manager instance"""
    global _vector_search_manager
    if _vector_search_manager is None:
        _vector_search_manager = VectorSearchManager()
    return _vector_search_manager

if __name__ == "__main__":
    # Test vector search functionality
    print("🔍 Testing Vector Search")
    print("=" * 50)
    
    try:
        vsm = get_vector_search_manager()
        
        if not vsm.is_available():
            print("❌ Vector search not available")
            exit(1)
        
        # Test indexing
        test_patient = {
            'id': 'test_001',
            'name': 'John Doe',
            'age': 45,
            'triage_level': 'Yellow',
            'status': 'Active',
            'notes': 'Chest pain, shortness of breath',
            'location': 'Zone A',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        indexed = vsm.index_patient(test_patient)
        print(f"✅ Patient indexed: {indexed}")
        
        # Test search
        results = vsm.search_similar_cases("chest pain patient")
        print(f"✅ Search results: {len(results)} found")
        
        for result in results[:3]:
            print(f"  - {result.source_type}: {result.similarity_score:.3f}")
        
        print("\n🎉 Vector search test completed!")
        
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        import traceback
        traceback.print_exc() 
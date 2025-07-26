#!/usr/bin/env python3
"""
Test script for vector search functionality
Tests indexing, searching, and debugging capabilities
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your Flask app runs on different port

def test_status():
    """Test the status endpoint"""
    print("🔍 Testing status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data}")
            return data
        else:
            print(f"❌ Status failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Status error: {e}")
        return None

def test_vector_search_debug():
    """Test vector search debug endpoint"""
    print("\n🔍 Testing vector search debug...")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/vector-search")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Vector search debug: {data}")
            return data
        else:
            print(f"❌ Vector search debug failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Vector search debug error: {e}")
        return None

def test_rebuild_vector_index():
    """Test rebuilding the vector index"""
    print("\n🔍 Testing vector index rebuild...")
    try:
        response = requests.post(f"{BASE_URL}/api/debug/rebuild-vector-index")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rebuild result: {data}")
            return data
        else:
            print(f"❌ Rebuild failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Rebuild error: {e}")
        return None

def test_add_missing_person():
    """Test adding a missing person with characteristics"""
    print("\n🔍 Testing add missing person...")
    
    # Sample missing person data with flat characteristics
    person_data = {
        "name": "Test Person",
        "age": 25,
        "description": "Test missing person for vector search",
        "contact_info": "test@example.com",
        "reported_by": "REUNIFICATION_COORDINATOR",
        "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",  # 1x1 pixel
        "ai_characteristics": {
            "gender": "female",
            "age_range": "young_adult",
            "hair_color": "brown",
            "hair_length": "medium",
            "eye_color": "blue",
            "skin_tone": "fair",
            "height": "5'6\"",
            "build": "average",
            "top_clothing": "blue shirt",
            "bottom_clothing": "black jeans",
            "accessories": "glasses",
            "distinctive_features": "small scar on left cheek"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/missing-persons/edge",
            json=person_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Added missing person: {data}")
            return data.get('person_id')
        else:
            print(f"❌ Add missing person failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Add missing person error: {e}")
        return None

def test_search_missing_persons(query):
    """Test searching for missing persons"""
    print(f"\n🔍 Testing search with query: '{query}'")
    
    search_data = {
        "query": query,
        "limit": 10
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/search/missing-persons",
            json=search_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search results: {data}")
            return data
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Search error: {e}")
        return None

def test_search_by_description():
    """Test searching by description"""
    print("\n🔍 Testing search by description...")
    
    description_data = {
        "description": "Looking for a young woman with brown hair, blue eyes, wearing glasses",
        "limit": 10
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/search/missing-persons-by-description",
            json=description_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Description search results: {data}")
            return data
        else:
            print(f"❌ Description search failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Description search error: {e}")
        return None

def main():
    """Run all tests"""
    print("🧪 Vector Search Test Suite")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Test 1: Check status
    status_data = test_status()
    
    # Test 2: Check vector search debug
    debug_data = test_vector_search_debug()
    
    # Test 3: Rebuild vector index
    rebuild_data = test_rebuild_vector_index()
    
    # Test 4: Add a test missing person
    person_id = test_add_missing_person()
    
    # Wait a moment for indexing
    if person_id:
        print("\n⏳ Waiting 2 seconds for indexing...")
        time.sleep(2)
    
    # Test 5: Search for missing persons
    test_search_missing_persons("female brown hair")
    test_search_missing_persons("blue eyes glasses")
    test_search_missing_persons("young woman")
    
    # Test 6: Search by description
    test_search_by_description()
    
    # Test 7: Check vector search debug again
    print("\n🔍 Checking vector search after tests...")
    final_debug = test_vector_search_debug()
    
    print("\n" + "=" * 50)
    print("🧪 Test Summary")
    print("=" * 50)
    
    if status_data:
        print(f"✅ Status: Vector search available: {status_data.get('vector_search', {}).get('available', False)}")
        print(f"✅ Status: Total documents: {status_data.get('vector_search', {}).get('total_documents', 0)}")
    
    if debug_data:
        print(f"✅ Debug: Total documents: {debug_data.get('total_documents', 0)}")
        print(f"✅ Debug: Document types: {debug_data.get('document_types', [])}")
    
    if rebuild_data:
        print(f"✅ Rebuild: Indexed {rebuild_data.get('indexed_count', 0)} documents")
    
    if person_id:
        print(f"✅ Added test person: {person_id}")
    
    if final_debug:
        print(f"✅ Final debug: Total documents: {final_debug.get('total_documents', 0)}")
    
    print("=" * 50)
    print("🎉 Test suite completed!")

if __name__ == "__main__":
    main() 
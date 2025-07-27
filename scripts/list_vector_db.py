#!/usr/bin/env python3
"""
List all documents in the vector database
Shows detailed information about each indexed document
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://emr.nomadichacker.com"  # Your Flask app URL

def list_all_vector_documents():
    """List all documents in the vector database"""
    print("🔍 Listing all documents in vector database...")
    print("=" * 60)
    
    try:
        # First check if vector search is available
        status_response = requests.get(f"{BASE_URL}/api/status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            vector_status = status_data.get('vector_search', {})
            print(f"📊 Vector Search Status:")
            print(f"   Available: {vector_status.get('available', False)}")
            print(f"   Total Documents: {vector_status.get('total_documents', 0)}")
            print(f"   Errors: {vector_status.get('errors', [])}")
            print()
        
        # Try to get debug info if available
        try:
            debug_response = requests.get(f"{BASE_URL}/api/debug/vector-search")
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                print(f"📋 Vector Database Contents:")
                print(f"   Total Documents: {debug_data.get('total_documents', 0)}")
                print(f"   Document Types: {debug_data.get('document_types', [])}")
                
                # Show sample documents
                sample_docs = debug_data.get('sample_documents', [])
                if sample_docs:
                    print(f"\n📄 Sample Documents:")
                    for i, doc in enumerate(sample_docs[:5], 1):  # Show first 5
                        print(f"   {i}. ID: {doc.get('id', 'N/A')}")
                        print(f"      Type: {doc.get('type', 'N/A')}")
                        print(f"      Content Preview: {doc.get('content', '')[:100]}...")
                        if doc.get('metadata'):
                            print(f"      Metadata: {json.dumps(doc['metadata'], indent=6)}")
                        print()
                
                return debug_data
            else:
                print(f"❌ Debug endpoint not available (404)")
        except Exception as e:
            print(f"❌ Debug endpoint error: {e}")
        
        # Fallback: Try to search with a very broad query to get all documents
        print("\n🔍 Attempting to retrieve documents via search...")
        
        # Try different search queries to get various document types
        search_queries = [
            "missing person",
            "patient",
            "soap note",
            "vitals",
            "video analysis"
        ]
        
        all_documents = []
        
        for query in search_queries:
            try:
                search_data = {
                    "query": query,
                    "limit": 50  # Get more results
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/search/missing-persons",
                    json=search_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    if results:
                        print(f"\n📄 Found {len(results)} documents for query '{query}':")
                        for result in results:
                            doc_info = {
                                'id': result.get('id'),
                                'type': result.get('source_type', 'unknown'),
                                'content': result.get('content', ''),
                                'metadata': result.get('metadata', {}),
                                'similarity_score': result.get('similarity_score', 0)
                            }
                            all_documents.append(doc_info)
                            
                            print(f"   ID: {doc_info['id']}")
                            print(f"   Type: {doc_info['type']}")
                            print(f"   Score: {doc_info['similarity_score']:.3f}")
                            print(f"   Content: {doc_info['content'][:100]}...")
                            if doc_info['metadata']:
                                print(f"   Metadata: {json.dumps(doc_info['metadata'], indent=6)}")
                            print()
                
            except Exception as e:
                print(f"❌ Search error for '{query}': {e}")
        
        # Also try the general search endpoint
        try:
            response = requests.post(
                f"{BASE_URL}/api/search/similar-cases",
                json={"query": "all", "limit": 50},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    print(f"\n📄 Found {len(results)} documents via similar-cases search:")
                    for result in results:
                        doc_info = {
                            'id': result.get('id'),
                            'type': result.get('source_type', 'unknown'),
                            'content': result.get('content', ''),
                            'metadata': result.get('metadata', {}),
                            'similarity_score': result.get('similarity_score', 0)
                        }
                        all_documents.append(doc_info)
                        
                        print(f"   ID: {doc_info['id']}")
                        print(f"   Type: {doc_info['type']}")
                        print(f"   Score: {doc_info['similarity_score']:.3f}")
                        print(f"   Content: {doc_info['content'][:100]}...")
                        if doc_info['metadata']:
                            print(f"   Metadata: {json.dumps(doc_info['metadata'], indent=6)}")
                        print()
        
        except Exception as e:
            print(f"❌ Similar-cases search error: {e}")
        
        # Summary
        print("=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        if all_documents:
            # Remove duplicates based on ID
            unique_docs = {}
            for doc in all_documents:
                if doc['id'] not in unique_docs:
                    unique_docs[doc['id']] = doc
            
            print(f"Total unique documents found: {len(unique_docs)}")
            
            # Group by type
            by_type = {}
            for doc in unique_docs.values():
                doc_type = doc['type']
                if doc_type not in by_type:
                    by_type[doc_type] = []
                by_type[doc_type].append(doc)
            
            print(f"Documents by type:")
            for doc_type, docs in by_type.items():
                print(f"   {doc_type}: {len(docs)} documents")
        else:
            print("No documents found in vector database")
        
        return all_documents
        
    except Exception as e:
        print(f"❌ Error listing vector database: {e}")
        return None

def main():
    """Main function"""
    print("🧪 Vector Database Lister")
    print("=" * 60)
    print(f"Target URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    documents = list_all_vector_documents()
    
    print("\n" + "=" * 60)
    print("🎉 Vector database listing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main() 
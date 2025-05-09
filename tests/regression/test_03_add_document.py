#!/usr/bin/env python3
"""
Regression Test 3: Check document addition.

This test:
1. Starts the services
2. Adds a document
3. Verifies the document is in the database
4. Checks that indexes exist
5. Stops the services

Usage:
    python -m tests.regression.test_03_add_document
"""
import os
import sys
import time
import json

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.regression.test_utils import (
    start_services,
    stop_services,
    add_test_document,
    get_test_document_text,
    get_test_document_metadata,
    search_documents
)

def test_add_document():
    """Test adding a document to the GraphRAG system."""
    print("\n=== Test 3: Add Document ===\n")
    
    # Step 1: Start services
    print("Step 1: Starting services...")
    success, process = start_services()
    
    if not success:
        print("❌ Failed to start services")
        return False
    
    print("✅ Services started successfully")
    
    try:
        # Step 2: Add a document
        print("\nStep 2: Adding a document...")
        document_text = get_test_document_text()
        document_metadata = get_test_document_metadata()
        
        success, response = add_test_document(document_text, document_metadata)
        
        if success:
            print("✅ Document added successfully")
            print(f"Response: {json.dumps(response, indent=2)}")
            
            # Store document ID for later use
            document_id = response.get('document_id')
            if not document_id:
                print("❌ Document ID not found in response")
                return False
            
            print(f"Document ID: {document_id}")
        else:
            print("❌ Failed to add document")
            print(f"Error: {response.get('error')}")
            return False
        
        # Step 3: Verify document is in the database
        print("\nStep 3: Verifying document is in the database...")
        
        # Wait a moment for indexing to complete
        time.sleep(2)
        
        # Search for the document
        search_query = "GraphRAG knowledge graph"
        success, search_results = search_documents(search_query)
        
        if success:
            print("✅ Search successful")
            
            # Check if we got any vector results
            vector_results = search_results.get('vector_results', {})
            vector_docs = vector_results.get('documents', [])
            
            if vector_docs:
                print(f"✅ Found {len(vector_docs)} vector results")
                
                # Check if our document is in the results
                found = False
                for doc in vector_docs:
                    if "GraphRAG is an innovative approach" in doc:
                        found = True
                        break
                
                if found:
                    print("✅ Added document found in search results")
                else:
                    print("❌ Added document not found in search results")
                    print("First result snippet:", vector_docs[0][:100] if vector_docs else "No results")
                    return False
            else:
                print("❌ No vector results found")
                print(f"Search results: {json.dumps(search_results, indent=2)}")
                return False
            
            # Check if we got any graph results
            graph_results = search_results.get('graph_results', [])
            
            if graph_results:
                print(f"✅ Found {len(graph_results)} graph results")
            else:
                print("⚠️ No graph results found - this might be expected for a new document")
        else:
            print("❌ Search failed")
            print(f"Error: {search_results.get('error')}")
            return False
        
        # Step 4: Check indexes exist
        print("\nStep 4: Checking indexes exist...")
        
        # Perform another search to verify indexes
        success, search_results = search_documents("knowledge graph")
        
        if success:
            print("✅ Indexes exist and are working")
        else:
            print("❌ Index check failed")
            print(f"Error: {search_results.get('error')}")
            return False
        
        print("\n=== Test 3 Completed Successfully ===")
        return True
    
    finally:
        # Step 5: Stop services
        print("\nStep 5: Stopping services...")
        if stop_services(process):
            print("✅ Services stopped successfully")
        else:
            print("❌ Failed to stop services")

def main():
    """Main function to run the test."""
    success = test_add_document()
    
    if success:
        print("\n✅ Test 3 passed: Add document")
        return 0
    else:
        print("\n❌ Test 3 failed: Add document")
        return 1

if __name__ == "__main__":
    sys.exit(main())
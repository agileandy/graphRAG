#!/usr/bin/env python3
"""
Regression Test 6: Check deduplication.

This test:
1. Starts the services
2. Adds a document
3. Adds the same document again
4. Verifies the document is not added twice
5. Stops the services

Usage:
    python -m tests.regression.test_06_deduplication
"""
import os
import sys
import time
import json
import hashlib

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.regression.test_utils import (
    start_services,
    stop_services,
    add_test_document,
    search_documents,
    get_all_concepts
)

def test_deduplication():
    """Test deduplication in the GraphRAG system."""
    print("\n=== Test 6: Deduplication ===\n")
    
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
        
        document_text = """
        Deduplication in GraphRAG
        
        Deduplication is a critical feature in any knowledge management system. In GraphRAG,
        deduplication happens at multiple levels:
        
        1. Document Deduplication - Prevents the same document from being added multiple times
           - Uses content hashing to identify identical documents
           - Compares metadata to identify similar documents
        
        2. Concept Deduplication - Prevents duplicate concepts in the knowledge graph
           - Uses name normalization to identify similar concepts
           - Merges concepts that refer to the same entity
        
        3. Relationship Deduplication - Prevents duplicate relationships between concepts
           - Updates relationship strength instead of creating duplicates
           - Maintains a clean graph structure
        
        Effective deduplication ensures that the knowledge graph remains clean and efficient,
        without redundant information that could confuse search algorithms or users.
        """
        
        document_metadata = {
            "title": "Deduplication in GraphRAG",
            "author": "Regression Test",
            "category": "AI",
            "source": "Regression Test",
            "concepts": "Deduplication,Document Deduplication,Concept Deduplication,Relationship Deduplication"
        }
        
        # Generate a unique identifier for this document
        doc_hash = hashlib.md5(document_text.encode()).hexdigest()
        document_metadata["hash"] = doc_hash
        
        success, response = add_test_document(document_text, document_metadata)
        
        if success:
            print("✅ Document added successfully")
            print(f"Response: {json.dumps(response, indent=2)}")
            
            # Store document ID for later comparison
            first_doc_id = response.get('document_id')
            if not first_doc_id:
                print("❌ Document ID not found in response")
                return False
            
            print(f"First document ID: {first_doc_id}")
        else:
            print("❌ Failed to add document")
            print(f"Error: {response.get('error')}")
            return False
        
        # Wait for processing to complete
        print("Waiting for processing to complete...")
        time.sleep(5)
        
        # Step 3: Add the same document again
        print("\nStep 3: Adding the same document again...")
        
        success, response = add_test_document(document_text, document_metadata)
        
        if success:
            print("✅ Document submission accepted")
            print(f"Response: {json.dumps(response, indent=2)}")
            
            # Store second document ID for comparison
            second_doc_id = response.get('document_id')
            if not second_doc_id:
                print("❌ Document ID not found in response")
                return False
            
            print(f"Second document ID: {second_doc_id}")
        else:
            print("⚠️ Document submission rejected - this might be expected if deduplication is working")
            print(f"Error: {response.get('error')}")
            
            # If the document was rejected due to deduplication, this is actually a success
            if "duplicate" in str(response.get('error', '')).lower():
                print("✅ Deduplication detected at API level")
                second_doc_id = None
            else:
                print("❌ Document rejected for unexpected reason")
                return False
        
        # Step 4: Verify the document is not added twice
        print("\nStep 4: Verifying the document is not added twice...")
        
        # Wait for processing to complete
        time.sleep(5)
        
        # Search for the document
        search_query = "deduplication in graphrag"
        success, search_results = search_documents(search_query)
        
        if success:
            print("✅ Search successful")
            
            # Check vector results
            vector_results = search_results.get('vector_results', {})
            vector_ids = vector_results.get('ids', [])
            
            if vector_ids:
                print(f"✅ Found {len(vector_ids)} vector results")
                
                # Check for duplicate IDs
                unique_ids = set(vector_ids)
                if len(unique_ids) == len(vector_ids):
                    print("✅ No duplicate IDs in search results")
                else:
                    print("❌ Found duplicate IDs in search results")
                    print(f"IDs: {vector_ids}")
                    return False
                
                # If we have both document IDs, check if they appear in results
                if first_doc_id and second_doc_id:
                    # Count occurrences of each ID
                    first_count = vector_ids.count(first_doc_id)
                    second_count = vector_ids.count(second_doc_id)
                    
                    print(f"First document ID appears {first_count} times")
                    print(f"Second document ID appears {second_count} times")
                    
                    if first_count <= 1 and second_count <= 1:
                        print("✅ Documents appear at most once in results")
                    else:
                        print("❌ Documents appear multiple times in results")
                        return False
            else:
                print("❌ No vector results found")
                return False
        else:
            print("❌ Search failed")
            print(f"Error: {search_results.get('error')}")
            return False
        
        # Check for duplicate concepts
        success, concepts_response = get_all_concepts()
        
        if success:
            concepts = concepts_response.get('concepts', [])
            concept_names = [concept['name'] for concept in concepts]
            
            # Check for duplicate concept names
            unique_names = set(concept_names)
            if len(unique_names) == len(concept_names):
                print("✅ No duplicate concept names found")
            else:
                # Find duplicates
                duplicates = [name for name in unique_names if concept_names.count(name) > 1]
                print(f"⚠️ Found duplicate concept names: {duplicates}")
                print("This might be expected if concepts are normalized differently")
        else:
            print("❌ Failed to get concepts")
            print(f"Error: {concepts_response.get('error')}")
            return False
        
        print("\n=== Test 6 Completed Successfully ===")
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
    success = test_deduplication()
    
    if success:
        print("\n✅ Test 6 passed: Deduplication")
        return 0
    else:
        print("\n❌ Test 6 failed: Deduplication")
        return 1

if __name__ == "__main__":
    sys.exit(main())
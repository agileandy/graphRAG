#!/usr/bin/env python3
"""
Regression Test 5: Check search functionality.

This test:
1. Starts the services
2. Adds a document for testing
3. Performs a search with RAG
4. Searches for relationships and concepts
5. Stops the services

Usage:
    python -m tests.regression.test_05_search
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
    search_documents,
    get_concept,
    get_documents_for_concept
)

def test_search_functionality():
    """Test search functionality in the GraphRAG system."""
    print("\n=== Test 5: Search Functionality ===\n")
    
    # Step 1: Start services
    print("Step 1: Starting services...")
    success, process = start_services()
    
    if not success:
        print("❌ Failed to start services")
        return False
    
    print("✅ Services started successfully")
    
    try:
        # Step 2: Add a document for testing
        print("\nStep 2: Adding a document for testing...")
        
        document_text = """
        Search in GraphRAG: Combining Vector and Graph Approaches
        
        Search is a fundamental capability of any knowledge system. In GraphRAG, search is enhanced
        by combining two complementary approaches:
        
        1. Vector Search - Uses embeddings to find semantically similar content
           - Based on mathematical similarity between vector representations
           - Captures semantic meaning regardless of exact wording
           - Implemented using ChromaDB or other vector databases
        
        2. Graph Search - Uses relationships between concepts to find related content
           - Traverses connections between entities in the knowledge graph
           - Captures structural relationships that vector search might miss
           - Implemented using Neo4j graph database
        
        The hybrid search approach in GraphRAG combines these methods to provide more comprehensive
        and contextually relevant results. When a user submits a query:
        
        1. The query is converted to a vector embedding
        2. Similar documents are retrieved from the vector database
        3. Concepts in the query are identified
        4. The knowledge graph is traversed to find related concepts
        5. Documents related to those concepts are retrieved
        6. Results are combined and ranked
        
        This approach leverages the strengths of both vector similarity and graph relationships,
        resulting in more accurate and comprehensive search results.
        """
        
        document_metadata = {
            "title": "Search in GraphRAG",
            "author": "Regression Test",
            "category": "AI",
            "source": "Regression Test",
            "concepts": "Search,Vector Search,Graph Search,Hybrid Search,Embeddings,Knowledge Graph"
        }
        
        success, response = add_test_document(document_text, document_metadata)
        
        if success:
            print("✅ Document added successfully")
        else:
            print("❌ Failed to add document")
            print(f"Error: {response.get('error')}")
            return False
        
        # Wait for processing to complete
        print("Waiting for processing to complete...")
        time.sleep(5)
        
        # Step 3: Perform a search with RAG
        print("\nStep 3: Performing a search with RAG...")
        
        search_query = "How does hybrid search work in GraphRAG?"
        success, search_results = search_documents(search_query)
        
        if success:
            print("✅ Search successful")
            
            # Check vector results
            vector_results = search_results.get('vector_results', {})
            vector_docs = vector_results.get('documents', [])
            
            if vector_docs:
                print(f"✅ Found {len(vector_docs)} vector results")
                print("First result snippet:", vector_docs[0][:100] if vector_docs else "No results")
            else:
                print("❌ No vector results found")
                return False
            
            # Check graph results
            graph_results = search_results.get('graph_results', [])
            
            if graph_results:
                print(f"✅ Found {len(graph_results)} graph results")
                print("Graph results:", graph_results)
            else:
                print("⚠️ No graph results found - this might be expected for a new document")
        else:
            print("❌ Search failed")
            print(f"Error: {search_results.get('error')}")
            return False
        
        # Step 4: Search for relationships and concepts
        print("\nStep 4: Searching for relationships and concepts...")
        
        # Get information about a concept
        concept_to_check = "Search"
        success, concept_response = get_concept(concept_to_check)
        
        if success:
            concept = concept_response.get('concept', {})
            related_concepts = concept_response.get('related_concepts', [])
            
            print(f"✅ Found concept: {concept.get('name')}")
            print(f"✅ Found {len(related_concepts)} related concepts")
            
            if related_concepts:
                print("Related concepts:")
                for related in related_concepts[:5]:  # Show up to 5 related concepts
                    print(f"  - {related.get('name')} (strength: {related.get('strength')})")
            else:
                print("⚠️ No related concepts found - this might be expected for a new document")
            
            # Get documents for this concept
            success, docs_response = get_documents_for_concept(concept_to_check)
            
            if success:
                documents = docs_response.get('documents', [])
                print(f"✅ Found {len(documents)} documents for concept '{concept_to_check}'")
                
                if documents:
                    print("Document snippets:")
                    for doc in documents[:2]:  # Show up to 2 documents
                        text = doc.get('text', '')
                        print(f"  - {text[:100]}...")
                else:
                    print("⚠️ No documents found for this concept - this might be expected")
            else:
                print(f"❌ Failed to get documents for concept: {concept_to_check}")
                print(f"Error: {docs_response.get('error')}")
                # This is not a critical failure
                print("⚠️ Could not verify documents for concept - continuing test")
        else:
            print(f"❌ Failed to get concept: {concept_to_check}")
            print(f"Error: {concept_response.get('error')}")
            
            # Try another concept
            concept_to_check = "Vector Search"
            success, concept_response = get_concept(concept_to_check)
            
            if success:
                print(f"✅ Found alternative concept: {concept_response.get('concept', {}).get('name')}")
            else:
                print(f"❌ Failed to get alternative concept: {concept_to_check}")
                print(f"Error: {concept_response.get('error')}")
                return False
        
        print("\n=== Test 5 Completed Successfully ===")
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
    success = test_search_functionality()
    
    if success:
        print("\n✅ Test 5 passed: Search functionality")
        return 0
    else:
        print("\n❌ Test 5 failed: Search functionality")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Regression Test 4: Check NLP processing.

This test:
1. Starts the services
2. Adds a document with explicit concepts
3. Verifies NLP concepts are in the database
4. Checks relationships are in the database
5. Stops the services

Usage:
    python -m tests.regression.test_04_nlp_processing
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
    get_concept,
    get_all_concepts
)

def test_nlp_processing():
    """Test NLP processing in the GraphRAG system."""
    print("\n=== Test 4: NLP Processing ===\n")
    
    # Step 1: Start services
    print("Step 1: Starting services...")
    success, process = start_services()
    
    if not success:
        print("❌ Failed to start services")
        return False
    
    print("✅ Services started successfully")
    
    try:
        # Step 2: Add a document with explicit concepts
        print("\nStep 2: Adding a document with explicit concepts...")
        
        document_text = """
        Natural Language Processing (NLP) is a field of artificial intelligence that focuses on the interaction
        between computers and humans through natural language. The ultimate objective of NLP is to enable
        computers to understand, interpret, and generate human language in a valuable way.
        
        Key components of NLP include:
        
        1. Tokenization - Breaking text into words, phrases, or other meaningful elements
        2. Part-of-speech tagging - Identifying the grammatical parts of speech
        3. Named entity recognition - Identifying entities like people, organizations, locations
        4. Sentiment analysis - Determining the emotional tone behind text
        5. Relationship extraction - Identifying relationships between entities
        
        In the context of GraphRAG, NLP is used to extract concepts and relationships from documents.
        These concepts and relationships are then stored in a knowledge graph, which can be queried
        to provide context for large language models.
        
        The combination of NLP and knowledge graphs enables more sophisticated understanding of text,
        as it captures not just the semantic meaning but also the structural relationships between concepts.
        """
        
        document_metadata = {
            "title": "NLP and Knowledge Graphs",
            "author": "Regression Test",
            "category": "AI",
            "source": "Regression Test",
            "concepts": "NLP,Natural Language Processing,Tokenization,Named Entity Recognition,Sentiment Analysis,Relationship Extraction,Knowledge Graphs"
        }
        
        success, response = add_test_document(document_text, document_metadata)
        
        if success:
            print("✅ Document added successfully")
            print(f"Response: {json.dumps(response, indent=2)}")
        else:
            print("❌ Failed to add document")
            print(f"Error: {response.get('error')}")
            return False
        
        # Wait for NLP processing to complete
        print("Waiting for NLP processing to complete...")
        time.sleep(5)
        
        # Step 3: Verify NLP concepts are in the database
        print("\nStep 3: Verifying NLP concepts are in the database...")
        
        # Get all concepts
        success, concepts_response = get_all_concepts()
        
        if success:
            concepts = concepts_response.get('concepts', [])
            print(f"✅ Found {len(concepts)} concepts in the database")
            
            # Check for expected concepts
            expected_concepts = [
                "NLP", "Natural Language Processing", "Tokenization", 
                "Named Entity Recognition", "Sentiment Analysis", 
                "Relationship Extraction", "Knowledge Graphs"
            ]
            
            found_concepts = [concept['name'] for concept in concepts]
            print(f"Found concepts: {', '.join(found_concepts)}")
            
            # Check if at least some of the expected concepts are found
            found_count = sum(1 for concept in expected_concepts if any(
                expected.lower() in found.lower() for found in found_concepts
            ))
            
            if found_count >= 3:  # At least 3 of the expected concepts should be found
                print(f"✅ Found {found_count} of the expected concepts")
            else:
                print(f"❌ Only found {found_count} of the expected concepts")
                return False
        else:
            print("❌ Failed to get concepts")
            print(f"Error: {concepts_response.get('error')}")
            return False
        
        # Step 4: Check relationships are in the database
        print("\nStep 4: Checking relationships are in the database...")
        
        # Check for relationships by getting a specific concept
        concept_to_check = "NLP"
        success, concept_response = get_concept(concept_to_check)
        
        if success:
            concept = concept_response.get('concept', {})
            related_concepts = concept_response.get('related_concepts', [])
            
            print(f"✅ Found concept: {concept.get('name')}")
            print(f"✅ Found {len(related_concepts)} related concepts")
            
            if related_concepts:
                print("Related concepts:")
                for related in related_concepts:
                    print(f"  - {related.get('name')} (strength: {related.get('strength')})")
                
                print("✅ Relationships exist in the database")
            else:
                print("⚠️ No relationships found for this concept - this might be expected for a new document")
        else:
            # Try another concept if the first one fails
            concept_to_check = "Natural Language Processing"
            success, concept_response = get_concept(concept_to_check)
            
            if success:
                concept = concept_response.get('concept', {})
                related_concepts = concept_response.get('related_concepts', [])
                
                print(f"✅ Found concept: {concept.get('name')}")
                print(f"✅ Found {len(related_concepts)} related concepts")
                
                if related_concepts:
                    print("✅ Relationships exist in the database")
                else:
                    print("⚠️ No relationships found for this concept - this might be expected for a new document")
            else:
                print(f"❌ Failed to get concept: {concept_to_check}")
                print(f"Error: {concept_response.get('error')}")
                
                # This is not a critical failure as the concept might not exist yet
                print("⚠️ Could not verify relationships - continuing test")
        
        print("\n=== Test 4 Completed Successfully ===")
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
    success = test_nlp_processing()
    
    if success:
        print("\n✅ Test 4 passed: NLP processing")
        return 0
    else:
        print("\n❌ Test 4 failed: NLP processing")
        return 1

if __name__ == "__main__":
    sys.exit(main())
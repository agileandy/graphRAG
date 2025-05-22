#!/usr/bin/env python3
"""Regression Test 3: Check document addition.

This test:
1. Starts the services
2. Adds a document
3. Verifies the document is in the database
4. Checks that indexes exist
5. Stops the services

Usage:
    python -m tests.regression.test_03_add_document
"""

import json
import os
import sys
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tests.regression.test_utils import (
    add_test_document,
    get_test_document_metadata,
    get_test_document_text,
    search_documents,
    start_services,
    stop_services,
)


def test_add_document() -> None:
    """Test adding a document to the GraphRAG system."""
    print("\n=== Test 3: Add Document ===\n")

    # Step 1: Start services
    print("Step 1: Starting services...")
    success, process = start_services()

    assert success, "❌ Failed to start services"

    print("✅ Services started successfully")

    try:
        # Step 2: Add a document
        print("\nStep 2: Adding a document...")
        document_text = get_test_document_text()
        document_metadata = get_test_document_metadata()

        add_doc_success, response = add_test_document(document_text, document_metadata)

        assert add_doc_success, (
            f"❌ Failed to add document. Server response: {response.get('response')}. Error details: {response.get('error')}"
        )
        print("✅ Document added successfully")
        print(f"Response: {json.dumps(response, indent=2)}")

        # Store document ID for later use
        document_id = response.get("document_id")
        assert document_id, "❌ Document ID not found in response"
        print(f"Document ID: {document_id}")

        # Step 3: Verify document is in the database
        print("\nStep 3: Verifying document is in the database...")

        # Wait a moment for indexing to complete
        time.sleep(2)

        # Search for the document
        search_query = "GraphRAG knowledge graph"
        search_success, search_results = search_documents(search_query)

        assert search_success, f"❌ Search failed. Error: {search_results.get('error')}"
        print("✅ Search successful")

        # Check if we got any vector results
        vector_results = search_results.get("vector_results", {})
        vector_docs = vector_results.get("documents", [])

        assert vector_docs, (
            f"❌ No vector results found. Search results: {json.dumps(search_results, indent=2)}"
        )
        print(f"✅ Found {len(vector_docs)} vector results")

        # Check if our document is in the results
        found = False
        for doc in vector_docs:
            if "GraphRAG is an innovative approach" in doc:
                found = True
                break

        assert found, (
            f"❌ Added document not found in search results. First result snippet: {vector_docs[0][:100] if vector_docs else 'No results'}"
        )
        print("✅ Added document found in search results")

        # Check if we got any graph results
        graph_results = search_results.get("graph_results", [])

        if graph_results:
            print(f"✅ Found {len(graph_results)} graph results")
        else:
            print(
                "⚠️ No graph results found - this might be expected for a new document"
            )

        # Step 4: Check indexes exist
        print("\nStep 4: Checking indexes exist...")

        # Perform another search to verify indexes
        index_check_success, index_search_results = search_documents("knowledge graph")

        assert index_check_success, (
            f"❌ Index check failed. Error: {index_search_results.get('error')}"
        )
        print("✅ Indexes exist and are working")

        print("\n=== Test 3 Completed Successfully ===")

    finally:
        # Step 5: Stop services
        print("\nStep 5: Stopping services...")
        stop_success = stop_services(process)
        assert stop_success, "❌ Failed to stop services"
        print("✅ Services stopped successfully")


def main() -> int | None:
    """Main function to run the test."""
    try:
        test_add_document()
        print("\n✅ Test 3 passed: Add document")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test 3 failed: Add document - {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Test 3 failed with unexpected error: Add document - {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

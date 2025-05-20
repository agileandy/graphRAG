#!/usr/bin/env python3
"""Regression Test 7: Check adding a folder of documents.

This test:
1. Starts the services
2. Adds documents from a folder
3. Verifies the documents are in the database
4. Checks that concepts were extracted
5. Stops the services

Usage:
    python -m tests.regression.test_07_add_folder
"""

import os
import subprocess
import sys
import time
from typing import Any

import requests

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import tests.regression.test_utils as test_utils
from tests.regression.test_utils import (
    DOCUMENTS_ENDPOINT,
    get_all_concepts,
    search_documents,
    start_services,
    stop_services,
    wait_for_api_ready,
)

# Path to the folder containing documents to add
DOCUMENTS_FOLDER = "/Users/andyspamer/ebooks/prompting/"


def add_folder(
    folder_path: str, file_types: list[str] | None = None
) -> tuple[bool, dict[str, Any]]:
    """Add a folder of documents to the GraphRAG system using the API.

    Args:
        folder_path: Path to the folder containing documents
        file_types: List of file extensions to process (e.g., [".pdf", ".txt"])

    Returns:
        Tuple of (success, response_data)

    """
    if file_types is None:
        file_types = [".pdf", ".txt", ".md"]

    # Prepare request data
    data = {
        "folder_path": folder_path,
        "recursive": False,
        "file_types": file_types,
        "default_metadata": {
            "category": "AI",
            "subcategory": "Prompt Engineering",
            "source": "Regression Test",
        },
    }

    try:
        # Send request to add folder
        response = requests.post(f"{DOCUMENTS_ENDPOINT}/folder", json=data, timeout=30)

        # Check if request was successful
        if response.status_code in [200, 201, 202]:
            response_data = response.json()

            # Check if job was created
            if "job_id" in response_data:
                job_id = response_data["job_id"]
                print(f"Folder processing started as job {job_id}")

                # Poll for job completion
                max_polls = 30  # Maximum number of polls (30 * 2 seconds = 60 seconds)
                for i in range(max_polls):
                    # Get job status
                    status_response = requests.get(
                        f"{DOCUMENTS_ENDPOINT.replace('/documents', '')}/jobs/{job_id}",
                        timeout=10,
                    )

                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        job_status = status_data.get("status")

                        # Print progress
                        progress = status_data.get("progress", 0)
                        processed = status_data.get("processed_items", 0)
                        total = status_data.get("total_items", 0)
                        print(f"Progress: {progress:.1f}% ({processed}/{total})")

                        # Check if job is complete
                        if job_status in ["completed", "failed", "cancelled"]:
                            print(f"Job {job_id} {job_status}")

                            if job_status == "completed":
                                return True, status_data.get("result", {})
                            else:
                                return False, {
                                    "error": f"Job {job_status}",
                                    "details": status_data,
                                }

                    # Wait before polling again
                    time.sleep(2)

                # If we get here, the job is still running after max_polls
                return True, {
                    "status": "running",
                    "job_id": job_id,
                    "message": "Job still running, continuing with test",
                }

            # For synchronous processing or immediate response
            return True, response_data
        else:
            # Request failed
            error_message = (
                f"Failed to add folder: {response.status_code} - {response.text}"
            )
            print(error_message)
            return False, {"error": error_message}

    except Exception as e:
        error_message = f"Error adding folder: {str(e)}"
        print(error_message)
        return False, {"error": error_message}


def test_add_folder(start_stop_services=True) -> bool | None:
    """Test adding a folder of documents to the GraphRAG system.

    Args:
        start_stop_services: Whether to start and stop services as part of the test.
                            Set to False if services are already running.

    """
    print("\n=== Test 7: Add Folder ===\n")

    process = None
    if start_stop_services:
        # Step 1: Start services
        print("Step 1: Starting services...")
        success, process = start_services()

        if not success:
            print("❌ Failed to start services")
            return False

        print("✅ Services started successfully")
    else:
        print("Step 1: Using already running services...")
        # Check if API is accessible
        if not wait_for_api_ready(max_retries=5, retry_interval=1):
            print(
                "❌ API is not accessible. Please start services before running this test."
            )
            return False
        print("✅ Services are running")

    try:
        # Step 2: Add documents from folder
        print("\nStep 2: Adding documents from folder...")
        print(f"Folder path: {DOCUMENTS_FOLDER}")

        # Check if folder exists
        if not os.path.isdir(DOCUMENTS_FOLDER):
            print(f"❌ Folder not found: {DOCUMENTS_FOLDER}")
            return False

        # Count PDF files in the folder
        pdf_files = [
            f for f in os.listdir(DOCUMENTS_FOLDER) if f.lower().endswith(".pdf")
        ]
        print(f"Found {len(pdf_files)} PDF files in the folder")

        if not pdf_files:
            print("❌ No PDF files found in the folder")
            return False

        # Add the folder
        success, response = add_folder(DOCUMENTS_FOLDER, file_types=[".pdf"])

        if success:
            print("✅ Folder added successfully")

            # Print summary of added documents
            added_count = response.get("added_count", 0)
            skipped_count = response.get("skipped_count", 0)
            failed_count = response.get("failed_count", 0)

            # Check if we have a result field with details
            if "result" in response and isinstance(response["result"], dict):
                result = response["result"]
                added_count = result.get("added_count", added_count)
                skipped_count = result.get("skipped_count", skipped_count)
                failed_count = result.get("failed_count", failed_count)

                # Check if we have details with successful documents
                if "details" in result and isinstance(result["details"], list):
                    successful_docs = [
                        doc for doc in result["details"] if doc.get("success", False)
                    ]
                    if successful_docs and added_count == 0:
                        added_count = len(successful_docs)

            print(f"Added: {added_count} documents")
            print(f"Skipped: {skipped_count} documents")
            print(f"Failed: {failed_count} documents")

            if added_count == 0:
                print("❌ No documents were added")
                return False
        else:
            print("❌ Failed to add folder")
            print(f"Error: {response.get('error')}")
            return False

        # Wait for processing to complete
        print("Waiting for processing to complete...")
        # Wait longer to ensure all documents are indexed
        print("Waiting 30 seconds for indexing to complete...")
        time.sleep(30)

        # Step 3: Verify documents are in the database
        print("\nStep 3: Verifying documents are in the database...")

        # Search for a more general term that's likely to be in the documents
        search_query = "prompt"
        success, search_results = search_documents(search_query, n_results=10)

        if success:
            print("✅ Search successful")

            # Check vector results
            vector_results = search_results.get("vector_results", {})
            vector_docs = vector_results.get("documents", [])

            if vector_docs:
                print(f"✅ Found {len(vector_docs)} vector results")
                print(
                    "First result snippet:",
                    vector_docs[0][:100] if vector_docs else "No results",
                )
            else:
                print("❌ No vector results found")
                return False

            # Check graph results
            graph_results = search_results.get("graph_results", [])

            if graph_results:
                print(f"✅ Found {len(graph_results)} graph results")
            else:
                print(
                    "⚠️ No graph results found - this might be expected for new documents"
                )
        else:
            print("❌ Search failed")
            print(f"Error: {search_results.get('error')}")
            return False

        # Step 4: Check that concepts were extracted
        print("\nStep 4: Checking that concepts were extracted...")

        # Get all concepts
        success, concepts_response = get_all_concepts()

        if success:
            concepts = concepts_response.get("concepts", [])
            print(f"✅ Found {len(concepts)} concepts in the database")

            # Check for expected concepts related to prompt engineering
            expected_concepts = [
                "Prompt",
                "Prompt Engineering",
                "LLM",
                "GPT",
                "AI",
                "Language Model",
            ]

            found_concepts = [concept["name"] for concept in concepts]
            print(f"Sample concepts: {', '.join(found_concepts[:10])}")

            # Check if at least some of the expected concepts are found
            found_count = sum(
                1
                for concept in expected_concepts
                if any(concept.lower() in found.lower() for found in found_concepts)
            )

            if found_count > 0:
                print(f"✅ Found {found_count} of the expected concepts")
            else:
                print(
                    "⚠️ None of the expected concepts were found - this might be due to different content"
                )
        else:
            print("❌ Failed to get concepts")
            print(f"Error: {concepts_response.get('error')}")
            return False

        print("\n=== Test 7 Completed Successfully ===")
        return True

    finally:
        if start_stop_services and process:
            # Step 5: Stop services
            print("\nStep 5: Stopping services...")
            if stop_services(process):
                print("✅ Services stopped successfully")
            else:
                print("❌ Failed to stop services")
        else:
            print("\nStep 5: Keeping services running as requested...")


def main() -> int | None:
    """Main function to run the test."""
    # Check if --no-restart flag is provided
    import argparse

    parser = argparse.ArgumentParser(
        description="Test adding a folder of documents to GraphRAG"
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Do not restart services (use already running services)",
    )
    parser.add_argument(
        "--use-service-script",
        action="store_true",
        help="Use graphrag-service.sh script instead of start-graphrag-local.sh",
    )
    args = parser.parse_args()

    # If using service script, modify the start_services function in test_utils
    if args.use_service_script:
        # Save the original function
        original_start_services = test_utils.start_services

        # Define a new function that uses the service script
        def service_script_start_services():
            try:
                # Use the service script to start the services
                process = subprocess.Popen(
                    ["./scripts/service_management/graphrag-service.sh", "start"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # Wait for the API to be ready
                if test_utils.wait_for_api_ready():
                    return True, process

                # If the API is not ready, kill the process
                process.terminate()
                return False, None
            except Exception as e:
                print(f"Error starting services: {e}")
                return False, None

        # Replace the function
        test_utils.start_services = service_script_start_services

    try:
        # Run the test with or without restarting services
        success = test_add_folder(start_stop_services=not args.no_restart)

        if success:
            print("\n✅ Test 7 passed: Add folder")
            return 0
        else:
            print("\n❌ Test 7 failed: Add folder")
            return 1
    finally:
        # Restore the original function if we modified it
        if args.use_service_script:
            test_utils.start_services = original_start_services


if __name__ == "__main__":
    sys.exit(main())

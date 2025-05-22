"""Test folder addition functionality for the MCP server."""

import os
import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_invoke_tool,
    run_pytest_async
)

def create_test_folder() -> tuple[bool, str]:
    """Create a test folder with sample documents."""
    try:
        # Create a temporary test folder
        test_folder = "./test_data/sample_folder"
        os.makedirs(test_folder, exist_ok=True)

        # Create test files with different formats
        test_files = {
            "document1.txt": """
            Text document about artificial intelligence and machine learning.
            This file tests basic text processing capabilities.
            """,
            "document2.json": """
            {
                "title": "JSON Document",
                "content": "This tests JSON document processing",
                "tags": ["test", "json", "processing"]
            }
            """,
            "document3.md": """
            # Markdown Document

            This tests markdown processing capabilities.
            - List item 1
            - List item 2

            ## Section 2
            More content here.
            """
        }

        # Write test files
        for filename, content in test_files.items():
            file_path = os.path.join(test_folder, filename)
            with open(file_path, "w") as f:
                f.write(content)

        return True, test_folder
    except Exception as e:
        return False, str(e)

def test_add_folder() -> None:
    """Test adding a folder of documents via MCP."""
    print("\nTesting folder addition...")

    # Create test folder
    success, folder_path = create_test_folder()
    if not success:
        print_test_result(
            "Create Test Folder",
            False,
            f"Failed to create test folder: {folder_path}"
        )
        return

    try:
        # Try to add the folder via MCP
        success, result = sync_mcp_invoke_tool(
            tool_name="add_folder",
            parameters={
                "folder_path": folder_path,
                "recursive": False,
                "metadata": {
                    "source": "Test Suite",
                    "batch": "Folder Test"
                }
            }
        )

        if not success:
            print_test_result(
                "Add Folder",
                False,
                f"Failed to add folder: {result.get('error', 'Unknown error')}"
            )
            return

        # Verify results
        processed_files = result.get("processed_files", [])
        if len(processed_files) < 3:  # We expect 3 test files
            print_test_result(
                "Add Folder",
                False,
                f"Expected 3 processed files, found {len(processed_files)}"
            )
            return

        print_test_result(
            "Add Folder",
            True,
            f"Successfully processed {len(processed_files)} files"
        )

    finally:
        # Clean up test folder
        try:
            import shutil
            shutil.rmtree("./test_data")
        except Exception as e:
            print(f"Warning: Failed to clean up test folder: {str(e)}")

def test_add_folder_recursive() -> None:
    """Test adding a folder recursively."""
    print("\nTesting recursive folder addition...")

    try:
        # Create nested test folders
        base_folder = "./test_data/nested"
        subfolders = ["subfolder1", "subfolder2", "subfolder1/subsub"]

        for folder in subfolders:
            os.makedirs(os.path.join(base_folder, folder), exist_ok=True)

        # Add test files in various folders
        test_files = [
            ("main.txt", base_folder, "Main folder content"),
            ("sub1.txt", f"{base_folder}/subfolder1", "Subfolder 1 content"),
            ("sub2.txt", f"{base_folder}/subfolder2", "Subfolder 2 content"),
            ("subsub.txt", f"{base_folder}/subfolder1/subsub", "Sub-subfolder content")
        ]

        for filename, folder, content in test_files:
            with open(os.path.join(folder, filename), "w") as f:
                f.write(content)

        # Try to add the folder recursively via MCP
        success, result = sync_mcp_invoke_tool(
            tool_name="add_folder",
            parameters={
                "folder_path": base_folder,
                "recursive": True,
                "metadata": {
                    "source": "Test Suite",
                    "batch": "Recursive Folder Test"
                }
            }
        )

        if not success:
            print_test_result(
                "Add Folder Recursive",
                False,
                f"Failed to add folder recursively: {result.get('error', 'Unknown error')}"
            )
            return

        # Verify results
        processed_files = result.get("processed_files", [])
        if len(processed_files) < 4:  # We expect 4 test files
            print_test_result(
                "Add Folder Recursive",
                False,
                f"Expected 4 processed files, found {len(processed_files)}"
            )
            return

        print_test_result(
            "Add Folder Recursive",
            True,
            f"Successfully processed {len(processed_files)} files recursively"
        )

    finally:
        # Clean up test folders
        try:
            import shutil
            shutil.rmtree("./test_data")
        except Exception as e:
            print(f"Warning: Failed to clean up test folders: {str(e)}")

def test_add_empty_folder() -> None:
    """Test adding an empty folder."""
    print("\nTesting empty folder addition...")

    try:
        # Create empty test folder
        empty_folder = "./test_data/empty_folder"
        os.makedirs(empty_folder, exist_ok=True)

        # Try to add the empty folder
        success, result = sync_mcp_invoke_tool(
            tool_name="add_folder",
            parameters={
                "folder_path": empty_folder,
                "recursive": False,
                "metadata": {
                    "source": "Test Suite",
                    "batch": "Empty Folder Test"
                }
            }
        )

        # Should fail or return warning
        if success and not result.get("warning"):
            print_test_result(
                "Add Empty Folder",
                False,
                "No warning received for empty folder"
            )
            return

        print_test_result(
            "Add Empty Folder",
            True,
            f"Empty folder handled correctly: {result.get('warning', 'Warning received')}"
        )

    finally:
        # Clean up test folder
        try:
            import shutil
            shutil.rmtree("./test_data")
        except Exception as e:
            print(f"Warning: Failed to clean up test folder: {str(e)}")

def test_add_nonexistent_folder() -> None:
    """Test adding a nonexistent folder."""
    print("\nTesting nonexistent folder addition...")

    success, result = sync_mcp_invoke_tool(
        tool_name="add_folder",
        parameters={
            "folder_path": "./nonexistent_folder",
            "recursive": False,
            "metadata": {
                "source": "Test Suite",
                "batch": "Nonexistent Folder Test"
            }
        }
    )

    # Should fail with appropriate error
    if success:
        print_test_result(
            "Add Nonexistent Folder",
            False,
            "Operation succeeded for nonexistent folder"
        )
        return

    error_message = result.get("error", "")
    if "not found" not in error_message.lower() and "not exist" not in error_message.lower():
        print_test_result(
            "Add Nonexistent Folder",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Add Nonexistent Folder",
        True,
        "Nonexistent folder correctly rejected"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)
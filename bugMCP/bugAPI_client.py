#!/usr/bin/env python3
"""Bug Tracking API Client.

This script provides a command-line interface to interact with the Bug Tracking API server.
"""

import argparse
import json
import os
import sys
from typing import Any

import requests

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import get_port


def add_bug(host: str, port: int, description: str, cause: str) -> dict[str, Any]:
    """Add a new bug."""
    url = f"http://{host}:{port}/bugs"
    data = {"description": description, "cause": cause}

    response = requests.post(url, json=data)
    response.raise_for_status()

    return response.json()


def update_bug(
    host: str,
    port: int,
    bug_id: int,
    status: str | None = None,
    resolution: str | None = None,
) -> dict[str, Any]:
    """Update an existing bug."""
    url = f"http://{host}:{port}/bugs/{bug_id}"
    data = {}

    if status:
        data["status"] = status

    if resolution:
        data["resolution"] = resolution

    response = requests.put(url, json=data)
    response.raise_for_status()

    return response.json()


def delete_bug(host: str, port: int, bug_id: int) -> dict[str, Any]:
    """Delete a bug."""
    url = f"http://{host}:{port}/bugs/{bug_id}"

    response = requests.delete(url)
    response.raise_for_status()

    return response.json()


def get_bug(host: str, port: int, bug_id: int) -> dict[str, Any]:
    """Get a specific bug."""
    url = f"http://{host}:{port}/bugs/{bug_id}"

    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def list_bugs(host: str, port: int) -> dict[str, Any]:
    """List all bugs."""
    url = f"http://{host}:{port}/bugs"

    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def interactive_mode(host: str, port: int) -> None:
    """Run in interactive mode."""
    while True:
        print("\nBug Tracking API Client")
        print("1. List bugs")
        print("2. Add bug")
        print("3. Update bug")
        print("4. Delete bug")
        print("5. Get bug")
        print("0. Exit")

        choice = input("\nEnter your choice: ")

        if choice == "0":
            break

        try:
            if choice == "1":
                result = list_bugs(host, port)
                print("\nBug List:")
                if result.get("total_records", 0) > 0:
                    for bug in result.get("bugs", []):
                        print(
                            f"ID: {bug['id']}, Status: {bug['status']}, Description: {bug['description']}"
                        )
                else:
                    print("No bugs found.")

            elif choice == "2":
                description = input("Enter bug description: ")
                cause = input("Enter bug cause: ")

                result = add_bug(host, port, description, cause)

                if result.get("status") == "success":
                    print(f"✅ Bug added successfully with ID: {result.get('bug_id')}")
                else:
                    print(f"❌ Error adding bug: {result.get('message')}")

            elif choice == "3":
                bug_id = int(input("Enter bug ID: "))
                status = input("Enter new status (open/fixed) or leave empty: ")
                resolution = input("Enter resolution or leave empty: ")

                if not status:
                    status = None

                if not resolution:
                    resolution = None

                result = update_bug(host, port, bug_id, status, resolution)

                if result.get("status") == "success":
                    print(f"✅ Bug updated successfully: {result.get('message')}")
                else:
                    print(f"❌ Error updating bug: {result.get('message')}")

            elif choice == "4":
                bug_id = int(input("Enter bug ID: "))

                result = delete_bug(host, port, bug_id)

                if result.get("status") == "success":
                    print(f"✅ Bug deleted successfully: {result.get('message')}")
                else:
                    print(f"❌ Error deleting bug: {result.get('message')}")

            elif choice == "5":
                bug_id = int(input("Enter bug ID: "))

                result = get_bug(host, port, bug_id)

                if result.get("status") == "success":
                    bug = result.get("bug", {})
                    print("\nBug Details:")
                    print(f"ID: {bug.get('id')}")
                    print(f"Description: {bug.get('description')}")
                    print(f"Cause: {bug.get('cause')}")
                    print(f"Status: {bug.get('status')}")
                    print(f"Resolution: {bug.get('resolution')}")
                else:
                    print(f"❌ Error getting bug: {result.get('message')}")

            else:
                print("Invalid choice. Please try again.")

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")

        except Exception as e:
            print(f"❌ Error: {e}")


def command_mode(host: str, port: int, args) -> None:
    """Run in command mode."""
    try:
        if args.action == "list":
            result = list_bugs(host, port)
            print(json.dumps(result, indent=2))

        elif args.action == "add":
            if not args.description or not args.cause:
                print("❌ Error: description and cause are required for add action")
                return

            result = add_bug(host, port, args.description, args.cause)
            print(json.dumps(result, indent=2))

        elif args.action == "update":
            if not args.id:
                print("❌ Error: id is required for update action")
                return

            result = update_bug(host, port, args.id, args.status, args.resolution)
            print(json.dumps(result, indent=2))

        elif args.action == "delete":
            if not args.id:
                print("❌ Error: id is required for delete action")
                return

            result = delete_bug(host, port, args.id)
            print(json.dumps(result, indent=2))

        elif args.action == "get":
            if not args.id:
                print("❌ Error: id is required for get action")
                return

            result = get_bug(host, port, args.id)
            print(json.dumps(result, indent=2))

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main() -> None:
    """Main function."""
    # Get bug_mcp_port from centralized configuration
    bug_mcp_port = get_port("bug_mcp")

    parser = argparse.ArgumentParser(description="Bug Tracking API Client")
    parser.add_argument("--host", type=str, default="localhost", help="API server host")
    parser.add_argument(
        "--port",
        type=int,
        default=bug_mcp_port,
        help=f"API server port (default: {bug_mcp_port})",
    )

    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # List bugs
    subparsers.add_parser("list", help="List all bugs")

    # Add bug
    add_parser = subparsers.add_parser("add", help="Add a new bug")
    add_parser.add_argument("--description", type=str, help="Bug description")
    add_parser.add_argument("--cause", type=str, help="Bug cause")

    # Update bug
    update_parser = subparsers.add_parser("update", help="Update an existing bug")
    update_parser.add_argument("--id", type=int, help="Bug ID")
    update_parser.add_argument(
        "--status", type=str, choices=["open", "fixed"], help="Bug status"
    )
    update_parser.add_argument("--resolution", type=str, help="Bug resolution")

    # Delete bug
    delete_parser = subparsers.add_parser("delete", help="Delete a bug")
    delete_parser.add_argument("--id", type=int, help="Bug ID")

    # Get bug
    get_parser = subparsers.add_parser("get", help="Get a specific bug")
    get_parser.add_argument("--id", type=int, help="Bug ID")

    args = parser.parse_args()

    if args.action:
        # Command mode
        command_mode(args.host, args.port, args)
    else:
        # Interactive mode
        interactive_mode(args.host, args.port)


if __name__ == "__main__":
    main()

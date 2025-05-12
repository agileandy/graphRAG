#!/usr/bin/env python3
"""
Client script for the Bug Tracking MCP server.

This script provides a command-line interface to interact with the Bug Tracking MCP server.
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, Any, List, Optional

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def connect_to_server(host: str, port: int):
    """Connect to the MCP server."""
    url = f"http://{host}:{port}"
    print(f"Connecting to MCP server at {url}...")
    
    try:
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            # Create a session
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                print("✅ Connected to MCP server")
                
                # List available tools
                tools = await session.list_tools()
                print(f"Available tools: {', '.join(tool.name for tool in tools)}")
                
                return session
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        return None

async def add_bug(session, description: str, cause: str):
    """Add a new bug."""
    result = await session.call_tool("add_bug", {
        "description": description,
        "cause": cause
    })
    
    return result

async def update_bug(session, bug_id: int, status: Optional[str] = None, resolution: Optional[str] = None):
    """Update an existing bug."""
    params = {"id": bug_id}
    
    if status:
        params["status"] = status
    
    if resolution:
        params["resolution"] = resolution
    
    result = await session.call_tool("update_bug", params)
    
    return result

async def delete_bug(session, bug_id: int):
    """Delete a bug."""
    result = await session.call_tool("delete_bug", {
        "id": bug_id
    })
    
    return result

async def get_bug(session, bug_id: int):
    """Get a specific bug."""
    result = await session.call_tool("get_bug", {
        "id": bug_id
    })
    
    return result

async def list_bugs(session):
    """List all bugs."""
    result = await session.call_tool("list_bugs", {})
    
    return result

async def interactive_mode(host: str, port: int):
    """Run in interactive mode."""
    session = await connect_to_server(host, port)
    
    if not session:
        return
    
    while True:
        print("\nBug Tracking MCP Client")
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
                result = await list_bugs(session)
                print("\nBug List:")
                if result.get("total_records", 0) > 0:
                    for bug in result.get("bugs", []):
                        print(f"ID: {bug['id']}, Status: {bug['status']}, Description: {bug['description']}")
                else:
                    print("No bugs found.")
            
            elif choice == "2":
                description = input("Enter bug description: ")
                cause = input("Enter bug cause: ")
                
                result = await add_bug(session, description, cause)
                
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
                
                result = await update_bug(session, bug_id, status, resolution)
                
                if result.get("status") == "success":
                    print(f"✅ Bug updated successfully: {result.get('message')}")
                else:
                    print(f"❌ Error updating bug: {result.get('message')}")
            
            elif choice == "4":
                bug_id = int(input("Enter bug ID: "))
                
                result = await delete_bug(session, bug_id)
                
                if result.get("status") == "success":
                    print(f"✅ Bug deleted successfully: {result.get('message')}")
                else:
                    print(f"❌ Error deleting bug: {result.get('message')}")
            
            elif choice == "5":
                bug_id = int(input("Enter bug ID: "))
                
                result = await get_bug(session, bug_id)
                
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
        
        except Exception as e:
            print(f"❌ Error: {e}")

async def command_mode(host: str, port: int, args):
    """Run in command mode."""
    session = await connect_to_server(host, port)
    
    if not session:
        return
    
    try:
        if args.action == "list":
            result = await list_bugs(session)
            print(json.dumps(result, indent=2))
        
        elif args.action == "add":
            if not args.description or not args.cause:
                print("❌ Error: description and cause are required for add action")
                return
            
            result = await add_bug(session, args.description, args.cause)
            print(json.dumps(result, indent=2))
        
        elif args.action == "update":
            if not args.id:
                print("❌ Error: id is required for update action")
                return
            
            result = await update_bug(session, args.id, args.status, args.resolution)
            print(json.dumps(result, indent=2))
        
        elif args.action == "delete":
            if not args.id:
                print("❌ Error: id is required for delete action")
                return
            
            result = await delete_bug(session, args.id)
            print(json.dumps(result, indent=2))
        
        elif args.action == "get":
            if not args.id:
                print("❌ Error: id is required for get action")
                return
            
            result = await get_bug(session, args.id)
            print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bug Tracking MCP Client")
    parser.add_argument("--host", type=str, default="localhost", help="MCP server host")
    parser.add_argument("--port", type=int, default=5005, help="MCP server port")
    
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")
    
    # List bugs
    list_parser = subparsers.add_parser("list", help="List all bugs")
    
    # Add bug
    add_parser = subparsers.add_parser("add", help="Add a new bug")
    add_parser.add_argument("--description", type=str, help="Bug description")
    add_parser.add_argument("--cause", type=str, help="Bug cause")
    
    # Update bug
    update_parser = subparsers.add_parser("update", help="Update an existing bug")
    update_parser.add_argument("--id", type=int, help="Bug ID")
    update_parser.add_argument("--status", type=str, choices=["open", "fixed"], help="Bug status")
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
        asyncio.run(command_mode(args.host, args.port, args))
    else:
        # Interactive mode
        asyncio.run(interactive_mode(args.host, args.port))

if __name__ == "__main__":
    main()
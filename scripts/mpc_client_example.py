"""
Example client for the GraphRAG MPC server.
"""
import json
import asyncio
import websockets
from typing import Dict, Any

async def send_message(websocket, action: str, **kwargs) -> Dict[str, Any]:
    """
    Send a message to the MPC server.

    Args:
        websocket: WebSocket connection
        action: Action to perform
        **kwargs: Additional parameters

    Returns:
        Server response
    """
    # Prepare message
    message = {
        'action': action,
        **kwargs
    }

    # Send message
    await websocket.send(json.dumps(message))

    # Receive response
    response = await websocket.recv()

    # Parse response
    return json.loads(response)

async def interactive_client(uri: str = "ws://localhost:8765"):
    """
    Run an interactive client for the MPC server.

    Args:
        uri: WebSocket URI
    """
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to MPC server.")
            print("\nGraphRAG MPC Client")
            print("===================")
            print("Available actions:")
            print("=== Search Tools ===")
            print("1. search - Hybrid search across the GraphRAG system")
            print("2. concept - Explore a concept")
            print("3. documents - Find documents for a concept")
            print("4. books-by-concept - Find books mentioning a concept")
            print("5. related-concepts - Find concepts related to a concept")
            print("6. passages-about-concept - Find passages about a concept")
            print("\n=== Document Addition Tools ===")
            print("7. add-document - Add a single document to the system")
            print("8. add-folder - Add a folder of documents to the system")
            print("\n0. exit - Exit the client")
            print()

            # Get available actions from server
            try:
                # Send an invalid action to get available actions
                response = await send_message(websocket, "get-available-actions")
                if 'available_actions' in response:
                    print("\nServer supports these actions:")
                    print(", ".join(response['available_actions']))
                    print()
            except:
                pass

            while True:
                action = input("Enter action (0-8): ")

                if action == "0" or action.lower() == "exit":
                    break

                if action == "1" or action.lower() == "search":
                    query = input("Enter search query: ")
                    n_results = int(input("Number of results (default: 5): ") or "5")
                    max_hops = int(input("Maximum hops (default: 2): ") or "2")

                    response = await send_message(
                        websocket,
                        "search",
                        query=query,
                        n_results=n_results,
                        max_hops=max_hops
                    )
                elif action == "2" or action.lower() == "concept":
                    concept_name = input("Enter concept name: ")

                    response = await send_message(
                        websocket,
                        "concept",
                        concept_name=concept_name
                    )
                elif action == "3" or action.lower() == "documents":
                    concept_name = input("Enter concept name: ")
                    limit = int(input("Maximum documents (default: 5): ") or "5")

                    response = await send_message(
                        websocket,
                        "documents",
                        concept_name=concept_name,
                        limit=limit
                    )
                elif action == "4" or action.lower() == "books-by-concept":
                    concept_name = input("Enter concept name: ")

                    response = await send_message(
                        websocket,
                        "books-by-concept",
                        concept_name=concept_name
                    )
                elif action == "5" or action.lower() == "related-concepts":
                    concept_name = input("Enter concept name: ")
                    max_hops = int(input("Maximum hops (default: 2): ") or "2")

                    response = await send_message(
                        websocket,
                        "related-concepts",
                        concept_name=concept_name,
                        max_hops=max_hops
                    )
                elif action == "6" or action.lower() == "passages-about-concept":
                    concept_name = input("Enter concept name: ")
                    limit = int(input("Maximum passages (default: 5): ") or "5")

                    response = await send_message(
                        websocket,
                        "passages-about-concept",
                        concept_name=concept_name,
                        limit=limit
                    )
                elif action == "7" or action.lower() == "add-document":
                    text = input("Enter document text: ")
                    title = input("Enter document title (optional): ")
                    source = input("Enter document source (optional): ")

                    metadata = {}
                    if title:
                        metadata["title"] = title
                    if source:
                        metadata["source"] = source

                    response = await send_message(
                        websocket,
                        "add-document",
                        text=text,
                        metadata=metadata
                    )
                elif action == "8" or action.lower() == "add-folder":
                    folder_path = input("Enter folder path: ")
                    recursive = input("Process subfolders? (y/n, default: n): ").lower() == 'y'
                    file_types_input = input("File types to process (comma-separated, default: .txt,.json): ")

                    file_types = [".txt", ".json"]
                    if file_types_input:
                        file_types = [ft.strip() if ft.strip().startswith('.') else f'.{ft.strip()}'
                                     for ft in file_types_input.split(',')]

                    response = await send_message(
                        websocket,
                        "add-folder",
                        folder_path=folder_path,
                        recursive=recursive,
                        file_types=file_types
                    )
                else:
                    print("Invalid action.")
                    continue

                # Print response
                print("\nResponse:")
                print(json.dumps(response, indent=2))
                print()
    except Exception as e:
        print(f"❌ Could not connect to {uri}")
        print(f"Error: {e}")
        print("Make sure the MPC server is running.")

async def non_interactive_client(uri: str, action: str, **kwargs):
    """
    Run a non-interactive client for the MPC server.

    Args:
        uri: WebSocket URI
        action: Action to perform
        **kwargs: Additional parameters for the action
    """
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to MPC server. Executing action: {action}")

            # Send message
            response = await send_message(websocket, action, **kwargs)

            # Print response
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            print()

            return response
    except Exception as e:
        print(f"❌ Could not connect to {uri}")
        print(f"Error: {e}")
        print("Make sure the MPC server is running.")
        return None

def main():
    """
    Main function to run the MPC client example.
    """
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Example client for the GraphRAG MPC server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")

    # Add action-specific arguments
    parser.add_argument("--action", type=str, help="Action to perform (search, concept, documents, books-by-concept, related-concepts, passages-about-concept, add-document, add-folder)")

    # Search arguments
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--n-results", type=int, default=5, help="Number of results")
    parser.add_argument("--max-hops", type=int, default=2, help="Maximum hops")

    # Concept arguments
    parser.add_argument("--concept-name", type=str, help="Concept name")
    parser.add_argument("--limit", type=int, default=5, help="Maximum documents/passages")

    # Document arguments
    parser.add_argument("--text", type=str, help="Document text")
    parser.add_argument("--title", type=str, help="Document title")
    parser.add_argument("--source", type=str, help="Document source")

    # Folder arguments
    parser.add_argument("--folder-path", type=str, help="Folder path")
    parser.add_argument("--recursive", type=bool, default=False, help="Process subfolders")
    parser.add_argument("--file-types", type=str, default=".txt,.json", help="File types to process (comma-separated)")

    args = parser.parse_args()

    # Build URI
    uri = f"ws://{args.host}:{args.port}"

    # Check if action is specified
    if args.action:
        # Prepare kwargs based on action
        kwargs = {}

        if args.action == "search":
            if not args.query:
                print("Error: --query is required for search action")
                return
            kwargs = {
                "query": args.query,
                "n_results": args.n_results,
                "max_hops": args.max_hops
            }
        elif args.action in ["concept", "books-by-concept"]:
            if not args.concept_name:
                print(f"Error: --concept-name is required for {args.action} action")
                return
            kwargs = {
                "concept_name": args.concept_name
            }
        elif args.action in ["documents", "passages-about-concept"]:
            if not args.concept_name:
                print(f"Error: --concept-name is required for {args.action} action")
                return
            kwargs = {
                "concept_name": args.concept_name,
                "limit": args.limit
            }
        elif args.action == "related-concepts":
            if not args.concept_name:
                print(f"Error: --concept-name is required for {args.action} action")
                return
            kwargs = {
                "concept_name": args.concept_name,
                "max_hops": args.max_hops
            }
        elif args.action == "add-document":
            if not args.text:
                print("Error: --text is required for add-document action")
                return
            metadata = {}
            if args.title:
                metadata["title"] = args.title
            if args.source:
                metadata["source"] = args.source
            kwargs = {
                "text": args.text,
                "metadata": metadata
            }
        elif args.action == "add-folder":
            if not args.folder_path:
                print("Error: --folder-path is required for add-folder action")
                return
            file_types = [ft.strip() if ft.strip().startswith('.') else f'.{ft.strip()}'
                         for ft in args.file_types.split(',')]
            kwargs = {
                "folder_path": args.folder_path,
                "recursive": args.recursive,
                "file_types": file_types
            }
        else:
            print(f"Error: Unknown action: {args.action}")
            return

        # Run non-interactive client
        asyncio.run(non_interactive_client(uri, args.action, **kwargs))
    else:
        # Run interactive client
        asyncio.run(interactive_client(uri))

if __name__ == "__main__":
    main()
import atexit
import json
import os
import socket
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_port

# File to store bugs
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bugs.json")

# Global storage
bugs = []
next_id = 1
VALID_STATUSES = {"open", "fixed"}


def save_bugs() -> None:
    """Save bugs to a JSON file."""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({"bugs": bugs, "next_id": next_id}, f, indent=2)
        print(f"Bugs saved to {DATA_FILE}")
    except Exception as e:
        print(f"Error saving bugs: {e}")


def load_bugs() -> None:
    """Load bugs from a JSON file."""
    global bugs, next_id
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
                bugs = data.get("bugs", [])
                next_id = data.get("next_id", 1)
            print(f"Loaded {len(bugs)} bugs from {DATA_FILE}")
        else:
            print(f"No data file found at {DATA_FILE}, starting with empty bug list")
    except Exception as e:
        print(f"Error loading bugs: {e}")


def parse_action(data):
    try:
        request = json.loads(data)
        if not isinstance(request, dict):
            raise ValueError("Invalid request format")

        required_fields = {
            "add": ["description", "cause"],
            "update": ["id"],
            "delete": ["id"],
            "get": ["id"],
            "list": [],
        }

        action = request.get("action")
        if not action:
            return {"status": "error", "message": "Missing action field"}

        if action not in required_fields:
            return {"status": "error", "message": f"Unknown action: {action}"}

        # Validate required fields for each action
        for field in required_fields.get(action, []):
            if field not in request:
                return {
                    "status": "error",
                    "message": f"Missing required field: {field}",
                }

        return {"status": "success", "payload": request}

    except (json.JSONDecodeError, ValueError) as e:
        return {"status": "error", "message": f"Invalid request: {str(e)}"}


def add_bug(description, cause):
    global next_id
    new_bug = {
        "id": next_id,
        "description": description,
        "cause": cause,
        "status": "open",
        "resolution": "",
    }
    bugs.append(new_bug)
    next_id += 1
    save_bugs()  # Save after adding a bug
    return new_bug


def update_bug(bug_id, updates):
    bug = next((b for b in bugs if b["id"] == bug_id), None)
    if not bug:
        return {"status": "error", "message": "Bug not found"}

    valid_fields = {"status", "resolution"}
    for field, value in updates.items():
        if field not in valid_fields:
            continue
        if field == "status" and value not in VALID_STATUSES:
            return {
                "status": "error",
                "message": f"Invalid status. Allowed values: {VALID_STATUSES}",
            }
        bug[field] = value

    save_bugs()  # Save after updating a bug
    return {"status": "success", "updated": True}


def delete_bug(bug_id):
    global bugs
    original_length = len(bugs)
    bugs = [b for b in bugs if b["id"] != bug_id]
    result = {"status": "success", "deleted": original_length > len(bugs)}
    if result["deleted"]:
        save_bugs()  # Save after deleting a bug
    return result


def handle_client_request(payload):
    action = payload.get("action")
    response = {}

    try:
        if action == "add":
            if "description" not in payload or "cause" not in payload:
                raise ValueError("Missing description or cause")
            new_bug = add_bug(payload["description"], payload["cause"])
            response = {
                "status": "success",
                "message": "Bug added successfully",
                "bug_id": new_bug["id"],
            }

        elif action == "update":
            required = ["id"]
            if not all(field in payload for field in required):
                raise ValueError("Missing required fields for update")

            bug_id = payload["id"]
            if "status" in payload and payload["status"] not in VALID_STATUSES:
                raise ValueError(f"Invalid status. Allowed values: {VALID_STATUSES}")

            # Find and update the bug
            for bug in bugs:
                if bug["id"] == bug_id:
                    if "status" in payload:
                        bug["status"] = payload["status"]
                    if "resolution" in payload:
                        bug["resolution"] = payload.get("resolution", "")
                    response = {
                        "status": "success",
                        "message": f"Updated bug {bug_id}",
                        "updated_fields": [k for k in payload.keys() if k != "id"],
                    }
                    save_bugs()  # Save after updating a bug
                    break
            else:
                raise ValueError(f"Bug ID {bug_id} not found")

        elif action == "delete":
            required = ["id"]
            if not all(field in payload for field in required):
                raise ValueError("Missing required fields for delete")
            result = delete_bug(payload["id"])
            response = {
                "status": "success" if result["deleted"] else "error",
                "message": f"Deleted {1 if result['deleted'] else 0} bugs"
                if result["deleted"]
                else "No bugs found with that ID",
            }

        elif action == "list":
            response = {"status": "success", "total_records": len(bugs), "bugs": bugs}

        elif action == "get":
            if "id" not in payload:
                raise ValueError("Missing ID field for get operation")
            bug_id = payload["id"]
            result = next((b for b in bugs if b["id"] == bug_id), None)
            if result:
                response = {"status": "success", "bug": result}
            else:
                response = {"status": "error", "message": f"Bug ID {bug_id} not found"}

        else:
            response = {"status": "error", "message": "Invalid action"}

    except ValueError as ve:
        response = {"status": "error", "message": str(ve)}
    except Exception as e:
        response = {"status": "error", "message": f"Unexpected error: {str(e)}"}

    return response


# Register save_bugs to be called when the program exits
atexit.register(save_bugs)

# Load bugs from file when starting
load_bugs()

# Get port from centralized configuration
bug_mcp_port = get_port("bug_mcp")

# TCP Server setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", bug_mcp_port))
server.listen(1)
print(f"Server listening on port {bug_mcp_port}...")
print(f"Data file: {DATA_FILE}")

try:
    while True:
        conn, addr = server.accept()
        print(f"Connected by {addr}")

        # Read all client data
        data = b""
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break
            data += chunk

        if data:
            # Process the request
            parsed = parse_action(data.decode())
            if parsed["status"] == "success":
                result = handle_client_request(parsed["payload"])
            else:
                result = parsed

            # Send response
            conn.sendall(json.dumps(result).encode())
            print(f"Response sent to {addr}")
        conn.close()

except KeyboardInterrupt:
    print("\nServer shutting down...")
finally:
    server.close()
    print("Server closed")
    # Save bugs one last time before exiting
    save_bugs()

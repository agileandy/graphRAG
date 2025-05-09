import socket
import json
import re

# Global storage
bugs = []
next_id = 1
VALID_STATUSES = {'open', 'fixed'}

def parse_action(data):
    try:
        request = json.loads(data)
        if not isinstance(request, dict):
            raise ValueError("Invalid request format")
            
        required_fields = {
            'add': ['description', 'cause'],
            'update': ['id'],
            'delete': ['id'],
            'get': ['id'],
            'list': []
        }

        action = request.get('action')
        if not action:
            return {'status': 'error', 'message': 'Missing action field'}

        if action not in required_fields:
            return {'status': 'error', 'message': f'Unknown action: {action}'}

        # Validate required fields for each action
        for field in required_fields.get(action, []):
            if field not in request:
                return {'status': 'error', 'message': f'Missing required field: {field}'}

        return {'status': 'success', 'payload': request}
    
    except (json.JSONDecodeError, ValueError) as e:
        return {'status': 'error', 'message': f'Invalid request: {str(e)}'}

def add_bug(description, cause):
    global next_id
    new_bug = {
        'id': next_id,
        'description': description,
        'cause': cause,
        'status': 'open',
        'resolution': ''
    }
    bugs.append(new_bug)
    next_id += 1
    return new_bug

def update_bug(attend_id, updates):
    attendee = next((a for a in attendees if a['id'] == attendee_id), None)
    if not attendee:
        return {'status': 'error', 'message': 'Attendee not found'}
    
    valid_fields = {'name', 'email', 'status'}
    for field, value in updates.items():
        if field not in valid_fields:
            continue
        if field == 'email' and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            return {'status': 'error', 'message': 'Invalid email format'}
        attendee[field] = value
    
    return {'status': 'success', 'updated': True}

def delete_attendee(attendee_id):
    global attendees
    original_length = len(attendees)
    attendees = [a for a in attendees if a['id'] != attendee_id]
    return {'status': 'success', 'deleted': original_length > len(attendees)}

def handle_client_request(payload):
    action = payload.get('action')
    response = {}

    try:
        if action == 'add':
            if 'description' not in payload or 'cause' not in payload:
                raise ValueError("Missing description or cause")
            new_bug = add_bug(payload['description'], payload['cause'])
            response = {
                'status': 'success',
                'message': 'Bug added successfully',
                'bug_id': new_bug['id']
            }

        elif action == 'update':
            required = ['id']
            if not all(field in payload for field in required):
                raise ValueError("Missing required fields for update")
            
            bug_id = payload['id']
            if 'status' in payload and payload['status'] not in VALID_STATUSES:
                raise ValueError(f"Invalid status. Allowed values: {VALID_STATUSES}")
            
            # Find and update the bug
            for bug in bugs:
                if bug['id'] == bug_id:
                    if 'status' in payload:
                        bug['status'] = payload['status']
                    if 'resolution' in payload:
                        bug['resolution'] = payload.get('resolution', '')
                    response = {
                        'status': 'success',
                        'message': f'Updated bug {bug_id}',
                        'updated_fields': [k for k in payload.keys() if k != 'id']
                    }
                    break
            else:
                raise ValueError(f"Bug ID {bug_id} not found")

        elif action == 'delete':
            required = ['id']
            if not all(field in payload for field in required):
                raise ValueError("Missing required fields for delete")
            deleted_count = len(bugs) - len([b for b in bugs if b['id'] != payload['id']])
            response = {
                'status': 'success' if deleted_count > 0 else 'error',
                'message': f"Deleted {deleted_count} bugs" if deleted_count > 0 else "No bugs found with that ID"
            }

        elif action == 'list':
            response = {
                'status': 'success',
                'total_records': len(attendees),
                'attendees': attendees
            }

        elif action == 'get':
            if 'id' not in payload:
                raise ValueError("Missing ID field for get operation")
            attendee_id = payload['id']
            result = next((a for a in attendees if a['id'] == attendee_id), None)
            if result:
                response = {'status': 'success', 'attendee': result}
            else:
                response = {'status': 'error', 'message': f"Attendee ID {attendee_id} not found"}

        else:
            response = {'status': 'error', 'message': 'Invalid action'}

    except ValueError as ve:
        response = {'status': 'error', 'message': str(ve)}
    except Exception as e:
        response = {'status': 'error', 'message': f'Unexpected error: {str(e)}'}

    return response

# TCP Server setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 5005))
server.listen(1)
print("Server listening on port 5000...")

try:
    while True:
        conn, addr = server.accept()
        print(f"Connected by {addr}")
        
        # Read all client data
        data = b''
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break
            data += chunk
        
        if data:
            # Process the request
            parsed = parse_action(data.decode())
            if parsed['status'] == 'success':
                result = handle_client_request(parsed['payload'])
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

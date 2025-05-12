import socket
import json

def add_bug(description, cause):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 5005))
        
        bug_data = {
            'action': 'add',
            'description': description,
            'cause': cause
        }
        
        s.sendall(json.dumps(bug_data).encode())
        
        data = b''
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            data += chunk
        
        s.close()
        return data.decode()
    except Exception as e:
        return f"Error adding bug: {str(e)}"

if __name__ == "__main__":
    description = "MPC server fails to start"
    cause = "The MPC server fails to start with no error message. The test_message_passing_server.py test fails with 'Failed to connect to Message Passing server at ws://localhost:8766'"
    
    result = add_bug(description, cause)
    print(result)

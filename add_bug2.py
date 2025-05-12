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
    description = "Port configuration mismatch between MCP server and tests"
    cause = "The MCP server is configured to run on port 8766 by default, but the tests were looking for it on port 8767. The test was updated to use port 8767 and the server was manually started on port 8767."
    
    result = add_bug(description, cause)
    print(result)

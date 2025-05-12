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
    description = "MCP server not running or using incorrect protocol"
    cause = "The server at port 8765 is not a Model Context Protocol server but a Message Passing Communication server. The test_model_context_server.py test fails with 'Missing required parameter: action'"

    result = add_bug(description, cause)
    print(result)

import socket
import os
import sys
import threading

BUFFER_SIZE = 1024

def create_data_channel():
    """Create a data socket and get its port number."""
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.bind(('', 0))  # Use any available port
    data_sock.listen(1)
    return data_sock, data_sock.getsockname()[1]

def handle_client_control_channel(control_sock, client_addr):
    print(f"Client connected from {client_addr}")
    try:
        while True:
            data = control_sock.recv(BUFFER_SIZE)
            if not data:
                break
                
            command_line = data.decode('utf-8').strip().lower()
            command_parts = command_line.split()
            command = command_parts[0] if command_parts else ''
            
            if command == "ls":
                try:
                    files = sorted(os.listdir("."))
                    response = "success " + " ".join(files) + "\r\n"
                    control_sock.sendall(response.encode('utf-8'))
                except Exception as e:
                    control_sock.sendall(f"failure {str(e)}\r\n".encode('utf-8'))
            
            elif command == "get" and len(command_parts) > 1:
                filename = command_parts[1]
                handle_get(control_sock, filename)
                
            elif command == "put" and len(command_parts) > 1:
                filename = command_parts[1]
                handle_put(control_sock, filename)
                
            elif command == "quit":
                control_sock.sendall(b"success Goodbye!\r\n")
                break
            else:
                control_sock.sendall(b"failure Invalid command\r\n")
    except Exception as e:
        print(f"Error handling client: {str(e)}")
    finally:
        print(f"Client {client_addr} disconnected")
        control_sock.close()

def handle_get(control_sock, filename):
    """Handle GET command: send file to client."""
    if not os.path.exists(filename):
        control_sock.sendall(f"failure File {filename} not found\r\n".encode('utf-8'))
        return

    try:
        # Create data channel
        data_sock, data_port = create_data_channel()
        
        # Send success and port number
        control_sock.sendall(f"success {data_port}\r\n".encode('utf-8'))
        
        # Accept client connection
        client_data_sock, _ = data_sock.accept()
        
        # Send file
        with open(filename, 'rb') as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                client_data_sock.sendall(data)
                
        print(f"Sent file {filename}")
        client_data_sock.close()
        data_sock.close()
        
    except Exception as e:
        control_sock.sendall(f"failure {str(e)}\r\n".encode('utf-8'))

def handle_put(control_sock, filename):
    """Handle PUT command: receive file from client."""
    try:
        # Create data channel
        data_sock, data_port = create_data_channel()
        
        # Send success and port number
        control_sock.sendall(f"success {data_port}\r\n".encode('utf-8'))
        
        # Accept client connection
        client_data_sock, _ = data_sock.accept()
        
        # Receive and write file
        with open(filename, 'wb') as f:
            while True:
                data = client_data_sock.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
                
        print(f"Received file {filename}")
        client_data_sock.close()
        data_sock.close()
        
    except Exception as e:
        control_sock.sendall(f"failure {str(e)}\r\n".encode('utf-8'))

def start_server(port):
    try:
        welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        welcome_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        welcome_sock.bind(("", port))
        welcome_sock.listen(5)
        print(f"FTP server listening on port {port}")

        while True:
            control_sock, client_addr = welcome_sock.accept()
            client_thread = threading.Thread(
                target=handle_client_control_channel, 
                args=(control_sock, client_addr)
            )
            client_thread.start()
            
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)
    finally:
        welcome_sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ftp_server.py <PORT>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if port <= 1024 or port > 65535:
            print("ERROR: Port number must be between 1024 and 65535.")
            sys.exit(1)
        start_server(port)
    except ValueError:
        print("ERROR: Port must be a number.")
        sys.exit(1)

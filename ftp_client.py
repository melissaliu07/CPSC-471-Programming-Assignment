import socket
import sys
import os

BUFFER_SIZE = 1024


def connect_data_channel(server_address, data_port):
    """Connect to server's data port."""
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((server_address, data_port))
    return data_sock


def handle_ls(control_sock):
    """List files on server."""
    try:
        control_sock.sendall(b"ls\r\n")
        response = control_sock.recv(BUFFER_SIZE)
        
        if response:
            response_text = response.decode('utf-8').strip()
            if response_text.startswith("success"):
                _, *files = response_text.split()
                print("\nServer files:")
                for file in files:
                    print(file)
            else:
                print("Error:", response_text)
    except Exception as e:
        print(f"Error in LS command: {str(e)}")


def handle_get(control_sock, server_address, filename):
    """Download file from server."""
    try:
        # Send GET command
        control_sock.sendall(f"get {filename}\r\n".encode('utf-8'))
        response = control_sock.recv(BUFFER_SIZE).decode('utf-8').strip()
        
        if not response.startswith("success"):
            print("Error:", response)
            return
        
        # Get data port and connect
        data_port = int(response.split()[1])
        data_sock = connect_data_channel(server_address, data_port)
        
        # Receive file
        total_bytes = 0
        with open(filename, 'wb') as f:
            while True:
                data = data_sock.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
                total_bytes += len(data)
        
        print(f"Downloaded {filename} ({total_bytes} bytes)")
        data_sock.close()
        
    except Exception as e:
        print(f"Error downloading file: {str(e)}")


def handle_put(control_sock, server_address, filename):
    """Upload file to server."""
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found")
        return
        
    try:
        # Send PUT command
        control_sock.sendall(f"put {filename}\r\n".encode('utf-8'))
        response = control_sock.recv(BUFFER_SIZE).decode('utf-8').strip()
        
        if not response.startswith("success"):
            print("Error:", response)
            return
        
        # Get data port and connect
        data_port = int(response.split()[1])
        data_sock = connect_data_channel(server_address, data_port)
        
        # Send file
        total_bytes = 0
        with open(filename, 'rb') as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                data_sock.sendall(data)
                total_bytes += len(data)
        
        print(f"Uploaded {filename} ({total_bytes} bytes)")
        data_sock.close()
        
    except Exception as e:
        print(f"Error uploading file: {str(e)}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python ftp_client.py <server_address> <server_port>")
        sys.exit(1)

    server_address = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("Error: Port must be an integer.")
        sys.exit(1)

    control_sock = None
    try:
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_sock.connect((server_address, server_port))
        print(f"Connected to {server_address} on port {server_port}")
        
        while True:
            try:
                user_input = input("ftp> ").strip()
                if not user_input:
                    continue

                command_parts = user_input.split()
                command = command_parts[0].lower()

                if command == "quit":
                    control_sock.sendall(b"quit\r\n")
                    print("Disconnected from server.")
                    break
                elif command == "ls":
                    handle_ls(control_sock)
                elif command == "get" and len(command_parts) == 2:
                    handle_get(control_sock, server_address, command_parts[1])
                elif command == "put" and len(command_parts) == 2:
                    handle_put(control_sock, server_address, command_parts[1])
                else:
                    print("Invalid command. Supported commands: ls, get <filename>, put <filename>, quit")
                    
            except Exception as e:
                print(f"Error in command execution: {str(e)}")
                break

    except Exception as e:
        print(f"Connection error: {str(e)}")
    finally:
        if control_sock:
            control_sock.close()


if __name__ == "__main__":
    main()

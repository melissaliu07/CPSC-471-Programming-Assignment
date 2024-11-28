import socket
import sys
import os

def print_usage():
    print("Usage: python ftp_client.py <server_address> <server_port>")

def connect_data_channel(data_port, server_address):
    """
    Connect to the server's data channel using the provided port.
    """
    try:
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((server_address, data_port))
        return data_sock
    except Exception as e:
        print(f"Error connecting to data channel: {e}")
        return None

def handle_ls(control_sock):
    """
    Handle the 'ls' command: List files on the server.
    """
    control_sock.sendall(b"LS\n")
    response = control_sock.recv(1024).decode('utf-8')
    print("Server response:\n" + response)

def handle_get(control_sock, server_address, filename):
    """
    Handle the 'get' command: Download a file from the server.
    """
    control_sock.sendall(f"GET {filename}\n".encode('utf-8'))
    response = control_sock.recv(1024).decode('utf-8').strip()

    if response.startswith("ERROR"):
        print(response)
        return

    print(response)
    data_port = int(control_sock.recv(1024).decode('utf-8').strip())
    data_sock = connect_data_channel(data_port, server_address)

    if data_sock:
        try:
            with open(filename, 'wb') as f:
                while True:
                    data = data_sock.recv(1024)
                    if not data:
                        break
                    f.write(data)
            print(f"File '{filename}' downloaded successfully.")
        except Exception as e:
            print(f"Error downloading file: {e}")
        finally:
            data_sock.close()

def handle_put(control_sock, server_address, filename):
    """
    Handle the 'put' command: Upload a file to the server.
    """
    if not os.path.exists(filename):
        print(f"ERROR: File '{filename}' does not exist.")
        return

    control_sock.sendall(f"PUT {filename}\n".encode('utf-8'))
    response = control_sock.recv(1024).decode('utf-8').strip()

    if response.startswith("ERROR"):
        print(response)
        return

    print(response)
    data_port = int(control_sock.recv(1024).decode('utf-8').strip())
    data_sock = connect_data_channel(data_port, server_address)

    if data_sock:
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                data_sock.sendall(data)
            print(f"File '{filename}' uploaded successfully.")
        except Exception as e:
            print(f"Error uploading file: {e}")
        finally:
            data_sock.close()

def main():
    # Validate command-line arguments
    if len(sys.argv) != 3:
        print_usage()
        sys.exit(1)

    server_address = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("Error: Port must be an integer.")
        print_usage()
        sys.exit(1)

    # Connect to the control channel
    try:
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_sock.connect((server_address, server_port))
        print(f"Connected to {server_address} on port {server_port}")
    except Exception as e:
        print(f"Error: Unable to connect to server: {e}")
        sys.exit(1)

    # Command interface
    while True:
        try:
            user_input = input("ftp> ").strip()
            if not user_input:
                continue

            command_parts = user_input.split()
            command = command_parts[0].lower()

            if command == "quit":
                control_sock.sendall(b"QUIT\n")
                print("Disconnected from server.")
                break
            elif command == "ls":
                handle_ls(control_sock)
            elif command == "get" and len(command_parts) == 2:
                handle_get(control_sock, server_address, command_parts[1])
            elif command == "put" and len(command_parts) == 2:
                handle_put(control_sock, server_address, command_parts[1])
            else:
                print("Invalid command. Supported commands: ls, get <filename>, put <filename>, quit.")
        except Exception as e:
            print(f"Error: {e}")
            break

    # Cleanup
    control_sock.close()

if __name__ == "__main__":
    main()


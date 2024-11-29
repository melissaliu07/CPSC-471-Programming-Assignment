import socket
import sys
import os
from ftp_helpers import (
    CMD_LIST, CMD_GET, CMD_PUT, CMD_QUIT,
    send_cmd, receive_response,
    recv_all, send_all, BUFFER_SIZE
)

def connect_data_channel(server_address, data_port):
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

def handle_list(control_sock, server_address):
    """
    Handle the LIST command to get the list of files from the server.
    """
    if not send_cmd(control_sock, CMD_LIST):
        print("Error: Failed to send LIST command.")
        return

    success, message = receive_response(control_sock)
    if not success:
        print(f"Error: {message}")
        return

    data_port = int(message)
    data_sock = connect_data_channel(server_address, data_port)
    if not data_sock:
        return

    try:
        data = recv_all(data_sock, BUFFER_SIZE).decode('utf-8')
        print("Files on server:\n" + data)
    finally:
        data_sock.close()

def handle_get(control_sock, server_address, filename):
    """
    Handle the GET command to download a file from the server.
    """
    if not send_cmd(control_sock, CMD_GET, filename):
        print("Error: Failed to send GET command.")
        return

    success, message = receive_response(control_sock)
    if not success:
        print(f"Error: {message}")
        return

    data_port = int(message)
    data_sock = connect_data_channel(server_address, data_port)
    if not data_sock:
        return

    try:
        with open(filename, 'wb') as f:
            print(f"Downloading '{filename}'...")
            while True:
                data = data_sock.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
        print(f"File '{filename}' downloaded successfully.")
    finally:
        data_sock.close()

def handle_put(control_sock, server_address, filename):
    """
    Handle the PUT command to upload a file to the server.
    """
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist.")
        return

    if not send_cmd(control_sock, CMD_PUT, filename):
        print("Error: Failed to send PUT command.")
        return

    success, message = receive_response(control_sock)
    if not success:
        print(f"Error: {message}")
        return

    data_port = int(message)
    data_sock = connect_data_channel(server_address, data_port)
    if not data_sock:
        return

    try:
        with open(filename, 'rb') as f:
            print(f"Uploading '{filename}'...")
            data = f.read()
            send_all(data_sock, data)
        print(f"File '{filename}' uploaded successfully.")
    finally:
        data_sock.close()

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

    try:
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_sock.connect((server_address, server_port))
        print(f"Connected to {server_address}:{server_port}")
    except Exception as e:
        print(f"Error: Unable to connect to server: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("ftp> ").strip()
            if not user_input:
                continue

            command_parts = user_input.split()
            command = command_parts[0].upper()

            if command == CMD_QUIT:
                if send_cmd(control_sock, CMD_QUIT):
                    print("Disconnected from server.")
                break
            elif command == CMD_LIST:
                handle_list(control_sock, server_address)
            elif command == CMD_GET and len(command_parts) == 2:
                handle_get(control_sock, server_address, command_parts[1])
            elif command == CMD_PUT and len(command_parts) == 2:
                handle_put(control_sock, server_address, command_parts[1])
            else:
                print("Invalid command. Supported commands: LIST, GET <filename>, PUT <filename>, QUIT.")
        except Exception as e:
            print(f"Error: {e}")
            break

    control_sock.close()

if __name__ == "__main__":
    main()

import socket
import os
import sys
import threading
from ftp_protocol import (
    CMD_LIST, CMD_GET, CMD_PUT, CMD_QUIT,
    create_data_socket, send_all, recv_all,
    send_cmd, recv_cmd, send_response, receive_response
)


def handle_client_control_channel(control_sock, client_addr):
    print(f"Client connected from {client_addr}")

    while True:
        try:
            # Receive command using recv_cmd
            command, args = recv_cmd(control_sock)
            if not command:
                break

            print(f"Received command: {command} with args {args}")
            if command == CMD_LIST:
                handle_ls(control_sock)
            elif command == CMD_GET:
                if not args:
                    send_response(control_sock, False, "Missing filename for 'GET'")
                else:
                    handle_get(control_sock, args[0])
            elif command == CMD_PUT:
                if not args:
                    send_response(control_sock, False, "Missing filename for 'PUT'")
                else:
                    handle_put(control_sock, args[0])
            elif command == CMD_QUIT:
                send_response(control_sock, True, "Disconnecting...")
                break
            else:
                send_response(control_sock, False, "Unknown command")
        except Exception as e:
            print(f"Error handling client command: {e}")
            break

    print(f"Client {client_addr} disconnected.")
    control_sock.close()


# Handle the "LIST" command
def handle_ls(control_sock):
    try:
        files = os.listdir(".")
        file_list = "\n".join(files) + "\n"
        send_response(control_sock, True, file_list)
    except Exception as e:
        send_response(control_sock, False, str(e))


# Handle the "GET" command
def handle_get(control_sock, filename):
    if not os.path.exists(filename):
        send_response(control_sock, False, "File not found")
        return

    send_response(control_sock, True, "Ready to send file")

    # Set up data channel
    data_sock, data_port = create_data_socket()
    if not data_sock:
        send_response(control_sock, False, "Failed to create data channel")
        return

    send_response(control_sock, True, str(data_port))

    client_data_sock, _ = data_sock.accept()
    with client_data_sock, data_sock:
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                send_all(client_data_sock, data)
            print(f"File '{filename}' sent successfully.")
        except Exception as e:
            print(f"Error sending file: {e}")


# Handle the "PUT" command
def handle_put(control_sock, filename):
    send_response(control_sock, True, "Ready to receive file")

    # Set up data channel
    data_sock, data_port = create_data_socket()
    if not data_sock:
        send_response(control_sock, False, "Failed to create data channel")
        return

    send_response(control_sock, True, str(data_port))

    client_data_sock, _ = data_sock.accept()
    with client_data_sock, data_sock:
        try:
            with open(filename, 'wb') as f:
                while True:
                    data = recv_all(client_data_sock, BUFFER_SIZE)
                    if not data:
                        break
                    f.write(data)
            print(f"File '{filename}' received successfully.")
        except Exception as e:
            print(f"Error receiving file: {e}")


# Main server function
def start_server(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as welcome_sock:
        welcome_sock.bind(("", port))
        welcome_sock.listen(5)
        print(f"FTP server listening on port {port}")

        while True:
            control_sock, client_addr = welcome_sock.accept()
            client_thread = threading.Thread(
                target=handle_client_control_channel, args=(control_sock, client_addr)
            )
            client_thread.start()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ftp_server.py <PORT>")
        sys.exit(1)

    port = int(sys.argv[1])
    if port <= 1024 or port > 65535:
        print("ERROR: Port number must be between 1024 and 65535.")
        sys.exit(1)

    start_server(port)


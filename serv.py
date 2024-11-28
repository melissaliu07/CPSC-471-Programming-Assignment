import socket
import os
import sys
import threading

# Function to handle client commands
def handle_client_control_channel(control_sock, client_addr):
    print(f"Client connected from {client_addr}")

    while True:
        try:
            # Receive command from the client
            command = control_sock.recv(1024).decode('utf-8').strip()
            if not command:
                break

            print(f"Received command: {command}")
            tokens = command.split()
            cmd = tokens[0].lower()

            if cmd == "ls":
                handle_ls(control_sock)
            elif cmd == "get":
                if len(tokens) < 2:
                    control_sock.sendall(b"ERROR: Missing filename for 'get'\n")
                else:
                    handle_get(control_sock, tokens[1])
            elif cmd == "put":
                if len(tokens) < 2:
                    control_sock.sendall(b"ERROR: Missing filename for 'put'\n")
                else:
                    handle_put(control_sock, tokens[1])
            elif cmd == "quit":
                control_sock.sendall(b"SUCCESS: Disconnecting...\n")
                break
            else:
                control_sock.sendall(b"ERROR: Unknown command\n")
        except Exception as e:
            print(f"Error handling client command: {e}")
            break

    print(f"Client {client_addr} disconnected.")
    control_sock.close()


# Handle the "ls" command
def handle_ls(control_sock):
    try:
        files = os.listdir(".")
        file_list = "\n".join(files) + "\n"
        control_sock.sendall(file_list.encode('utf-8'))
    except Exception as e:
        control_sock.sendall(f"ERROR: {e}\n".encode('utf-8'))


# Handle the "get" command
def handle_get(control_sock, filename):
    if not os.path.exists(filename):
        control_sock.sendall(b"ERROR: File not found\n")
        return

    control_sock.sendall(b"SUCCESS: Ready to send file\n")

    # Set up data channel
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_sock:
        data_sock.bind(("", 0))
        data_sock.listen(1)
        data_port = data_sock.getsockname()[1]
        control_sock.sendall(f"{data_port}\n".encode('utf-8'))

        client_data_sock, _ = data_sock.accept()
        with client_data_sock:
            try:
                with open(filename, 'rb') as f:
                    data = f.read()
                    client_data_sock.sendall(data)
                print(f"File '{filename}' sent successfully.")
            except Exception as e:
                print(f"Error sending file: {e}")


# Handle the "put" command
def handle_put(control_sock, filename):
    control_sock.sendall(b"SUCCESS: Ready to receive file\n")

    # Set up data channel
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_sock:
        data_sock.bind(("", 0))
        data_sock.listen(1)
        data_port = data_sock.getsockname()[1]
        control_sock.sendall(f"{data_port}\n".encode('utf-8'))

        client_data_sock, _ = data_sock.accept()
        with client_data_sock:
            try:
                with open(filename, 'wb') as f:
                    while True:
                        data = client_data_sock.recv(1024)
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
        print("Usage: python serv.py <PORT>")
        sys.exit(1)

    port = int(sys.argv[1])
    if port <= 1024 or port > 65535:
        print("ERROR: Port number must be between 1024 and 65535.")
        sys.exit(1)

    start_server(port)


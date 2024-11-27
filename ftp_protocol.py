import socket

# Commands list:
CMD_LIST = "LIST"
CMD_GET = "GET"
CMD_PUT = "PUT"
CMD_QUIT = "QUIT"

# Header and Buffer sizes
HEADER_SIZE = 10
BUFFER_SIZE = 65536

# Response messages
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"

# Create 10 byte header:
def create_header(size):
    size_str = str(size)
    while len(size_str) < HEADER_SIZE:
        size_str = "0" + size_str
    return size_str

# Parse 10 byte header for file size:
def parse_header(header):
    try:
        return int(header)
    except ValueError:
        return 0

# For list, get, put, generate an ephemeral port; returns socket, port number
def create_data_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))  # Bind to ephemeral port
        sock.listen(1)
        return sock, sock.getsockname()[1]
    except socket.error:
        return None, None

# Problem 1: ensures all data is sent
def send_all(sock, data):
    bytes_sent = 0
    while bytes_sent < len(data):
        sent = sock.send(data[bytes_sent:])
        if sent == 0:
            return False
        bytes_sent += sent
    return True

# Prolem 2: ensures all data is received
def recv_all(sock, size):
    data = ""
    while len(data) < size:
        chunk = sock.recv(min(size - len(data), BUFFER_SIZE))
        if not chunk:
            return None
        data += chunk
    return data

#Transfer commands from client to server
def send_cmd(control_sock, command, *args):
    cmd_str = f"{command} {' '.join(map(str, args))}"
    return send_all(control_sock, cmd_str)

# Return (command, [arguments])
def recv_cmd(control_sock):
    """
    Required by: "Control channel... is used to transfer all commands"
    Returns: (command, [arguments])
    """
    data = recv_all(control_sock, BUFFER_SIZE)
    if not data:
        return None, []
    parts = data.strip().split()
    return parts[0] if parts else None, parts[1:]

# Server prints out success/ failure
def send_response(control_sock, success, message=""):
    response = SUCCESS if success else FAILURE
    if message:
        response += f" {message}"
    return send_all(control_sock, response)

# Server to client status/error messages
def receive_response(control_sock):
    data = recv_all(control_sock, BUFFER_SIZE)
    if not data:
        return False, "Connection lost"
    parts = data.strip().split(None, 1)
    success = parts[0] == SUCCESS
    message = parts[1] if len(parts) > 1 else ""
    return success, message

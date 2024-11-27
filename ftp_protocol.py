import socket

# Command codes
CMD_LIST = "LIST"
CMD_GET = "GET"
CMD_PUT = "PUT"
CMD_PORT = "PORT"
CMD_QUIT = "QUIT"

# Buffer sizes
HEADER_SIZE = 10
BUFFER_SIZE = 65536

# Response codes
RESP_OK = "200"
RESP_ERROR = "500"

import socket

HOST = "0.0.0.0"
PORT = 7213

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(128)

    print(f"Server listening on {HOST}:{PORT}...", flush=True)

    while True:
        connection, address = server.accept()

        with connection:
            print(f"Connected: {address}", flush=True)

            connection.sendall(b"Connected to server.\n")

            print(f"Response sent to: {address}", flush=True)

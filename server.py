import socket
from tkinter import EXCEPTION

host = "127.0.0.1"
port = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}")

    conn, adrs = server_socket.accept()
    print(f"client connected by {adrs}")

    
try:
    data = conn.recv(1024)
    if not data:
        exit()
    print(f"Received message: {data.decode()}")

    response = "Message received"
    conn.sendall(response.encode())
    conn.close()
except EXCEPTION as e:
    print(f"Error: {e}")


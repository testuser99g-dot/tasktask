import socket
from tkinter import EXCEPTION


host = "127.0.0.1"
port = 12345

try:
        # Create a TCP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect to the server
        client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")

        # Send a message to the server
        message = "Hello, Server!"
        client_socket.sendall(message.encode())
        print(f"Sent message: {message}")

        data = client_socket.recv(1024)
        if data:
            print(f"Received from server: {data.decode()}")
        else:
            print("No response received from server")

    
except EXCEPTION as e:
        print(f"Socket error: {e}")
    
try:
    client_socket.close()
    print("Client socket closed")
except NameError:
    pass  # Socket was never created
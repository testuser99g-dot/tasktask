# ssl_test_client.py
import socket
import ssl

HOST = '127.0.0.1'
PORT = 12345

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

with socket.create_connection((HOST, PORT)) as sock:
    with context.wrap_socket(sock, server_hostname=HOST) as ssock:
        print("[+] Connected to secure server")
        print("[Server]:", ssock.recv(1024).decode())
        ssock.send(b"Hi Server, I'm SSL client.")

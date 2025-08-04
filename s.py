# ssl_test_server.py
import socket
import ssl

HOST = '127.0.0.1'
PORT = 12345

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
    sock.bind((HOST, PORT))
    sock.listen(5)
    print("[+] Server listening...")

    with context.wrap_socket(sock, server_side=True) as ssock:
        conn, addr = ssock.accept()
        print(f"[+] Connection from {addr}")
        conn.send(b"Hello Secure Client!")
        data = conn.recv(1024)
        print(f"[Client]: {data.decode()}")
        conn.close()

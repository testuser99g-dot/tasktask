import socket
import ssl
import threading
import os

HOST = '127.0.0.1'
PORT = 12345

clients = []
lock = threading.Lock()

def broadcast_message(message, sender_conn):
    with lock:
        for client in clients[:]:
            conn, username = client
            if conn != sender_conn:
                try:
                    conn.sendall(f"{message}".encode())
                except:
                    conn.close()
                    clients.remove(client)

def broadcast_file(filename, filedata, sender_conn):
    with lock:
        for client in clients[:]:
            conn, username = client
            if conn != sender_conn:
                try:
                    conn.sendall(f"FILE:{filename}:{len(filedata)}".encode())
                    ack = conn.recv(1024).decode()
                    if ack == "READY":
                        conn.sendall(filedata)
                except:
                    conn.close()
                    clients.remove(client)

def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")
    try:
        conn.send(b"Enter your username: ")
        username = conn.recv(1024).decode().strip()

        with lock:
            clients.append((conn, username))

        while True:
            data = conn.recv(1024)
            if not data:
                break

            msg = data.decode()

            if msg.lower() == "exit":
                break

            if msg.startswith("FILE:"):
                _, filename, filesize = msg.split(":")
                filesize = int(filesize)
                conn.send(b"READY")
                filedata = b''
                while len(filedata) < filesize:
                    chunk = conn.recv(min(4096, filesize - len(filedata)))
                    if not chunk:
                        break
                    filedata += chunk
                broadcast_file(filename, filedata, conn)
                print(f"[FILE] {username} sent {filename}")
            else:
                broadcast_message(f"{username}: {msg}", conn)

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")
    finally:
        with lock:
            for client in clients[:]:
                if client[0] == conn:
                    clients.remove(client)
                    break
        conn.close()
        print(f"[-] Disconnected {addr}")

def start_server():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind((HOST, PORT))
        server_sock.listen()
        print(f"[+] Secure Chat Server running on {HOST}:{PORT}")

        with context.wrap_socket(server_sock, server_side=True) as ssock:
            while True:
                try:
                    client_conn, addr = ssock.accept()
                    threading.Thread(target=handle_client, args=(client_conn, addr), daemon=True).start()
                except KeyboardInterrupt:
                    print("\n[!] Server shutting down.")
                    break

if __name__ == "__main__":
    start_server()

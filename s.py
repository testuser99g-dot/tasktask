import socket
import ssl
import threading
import os
from socket import timeout

HOST = '127.0.0.1'
PORT = 12345
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

clients = []
lock = threading.Lock()

def broadcast_message(message, sender_conn):
    with lock:
        for client in clients[:]:
            conn, username = client
            if conn != sender_conn:
                try:
                    conn.sendall(f"{message}".encode('utf-8'))
                except (ConnectionResetError, BrokenPipeError):
                    conn.close()
                    clients.remove(client)

def broadcast_file(filename, filedata, sender_conn):
    with lock:
        for client in clients[:]:
            conn, username = client
            if conn != sender_conn:
                try:
                    conn.sendall(f"FILE:{filename}:{len(filedata)}".encode('utf-8'))
                    conn.settimeout(5)  # Timeout for receiving READY
                    ack = conn.recv(1024).decode('utf-8')
                    if ack == "READY":
                        conn.sendall(filedata)
                except (ConnectionResetError, BrokenPipeError, timeout):
                    conn.close()
                    clients.remove(client)
                finally:
                    conn.settimeout(None)

def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")
    try:
        conn.send(b"Enter your username: ")
        username = conn.recv(1024).decode('utf-8', errors='ignore').strip()

        with lock:
            clients.append((conn, username))

        while True:
            conn.settimeout(60)  # Timeout for receiving data
            data = conn.recv(1024)
            if not data:
                break

            try:
                msg = data.decode('utf-8')
            except UnicodeDecodeError:
                print(f"[!] Invalid data from {addr}")
                continue

            if msg.lower() == "exit":
                break

            if msg.startswith("FILE:"):
                try:
                    _, filename, filesize = msg.split(":")
                    filesize = int(filesize)
                    if filesize > MAX_FILE_SIZE:
                        conn.send(b"ERROR: File too large")
                        continue
                    conn.send(b"READY")
                    filedata = b''
                    conn.settimeout(30)  # Timeout for file transfer
                    while len(filedata) < filesize:
                        chunk = conn.recv(min(4096, filesize - len(filedata)))
                        if not chunk:
                            break
                        filedata += chunk
                    if len(filedata) == filesize:
                        broadcast_file(filename, filedata, conn)
                        conn.send(b"FILE_SENT")
                        print(f"[FILE] {username} sent {filename}")
                    else:
                        conn.send(b"ERROR: Incomplete file")
                except ValueError:
                    conn.send(b"ERROR: Invalid file format")
            else:
                broadcast_message(f"{username}: {msg}", conn)

    except (ConnectionResetError, BrokenPipeError, timeout) as e:
        print(f"[!] Connection error with {addr}: {e}")
    except Exception as e:
        print(f"[!] Unexpected error with {addr}: {e}")
    finally:
        with lock:
            for client in clients[:]:
                if client[0] == conn:
                    clients.remove(client)
                    break
        conn.close()
        print(f"[-] Disconnected {addr}")

def start_server():
    try:
        if not (os.path.exists("cert.pem") and os.path.exists("key.pem")):
            raise FileNotFoundError("SSL certificate or key file missing")
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse port
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
    except Exception as e:
        print(f"[!] Server error: {e}")
    finally:
        server_sock.close()

if __name__ == "__main__":
    start_server()

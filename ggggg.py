import socket
import ssl
import threading
import os
import json
import bcrypt
import logging
from socket import timeout

HOST = '127.0.0.1'
PORT = 12345
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

clients = []
lock = threading.Lock()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load users from configuration file
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)['users']
    except FileNotFoundError:
        logging.error("users.json not found")
        return []

def verify_credentials(username, password, users):
    for user in users:
        if user['username'] == username:
            stored_hash = user['password_hash'].encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    return False

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
                    conn.settimeout(5)
                    ack = conn.recv(1024).decode('utf-8')
                    if ack == "READY":
                        conn.sendall(filedata)
                except (ConnectionResetError, BrokenPipeError, timeout):
                    conn.close()
                    clients.remove(client)
                finally:
                    conn.settimeout(None)

def handle_client(conn, addr):
    logging.info(f"[+] Connection from {addr}")
    try:
        # Authentication phase
        conn.settimeout(10)  # Timeout for authentication
        conn.send(b"AUTH_REQUEST")
        data = conn.recv(1024).decode('utf-8', errors='ignore')
        if not data.startswith("AUTH:"):
            conn.send(b"AUTH_FAILED")
            logging.warning(f"[!] Invalid auth format from {addr}")
            return
        try:
            _, username, password = data.split(":", 2)
        except ValueError:
            conn.send(b"AUTH_FAILED")
            logging.warning(f"[!] Malformed auth data from {addr}")
            return

        users = load_users()
        if verify_credentials(username, password, users):
            conn.send(b"AUTH_SUCCESS")
            logging.info(f"[AUTH] {username} authenticated successfully from {addr}")
        else:
            conn.send(b"AUTH_FAILED")
            logging.warning(f"[AUTH] Failed authentication for {username} from {addr}")
            return

        # Proceed with normal chat behavior
        with lock:
            clients.append((conn, username))

        while True:
            conn.settimeout(60)
            data = conn.recv(1024)
            if not data:
                break
            try:
                msg = data.decode('utf-8')
            except UnicodeDecodeError:
                logging.error(f"[!] Invalid data from {addr}")
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
                    conn.settimeout(30)
                    while len(filedata) < filesize:
                        chunk = conn.recv(min(4096, filesize - len(filedata)))
                        if not chunk:
                            break
                        filedata += chunk
                    if len(filedata) == filesize:
                        broadcast_file(filename, filedata, conn)
                        conn.send(b"FILE_SENT")
                        logging.info(f"[FILE] {username} sent {filename}")
                    else:
                        conn.send(b"ERROR: Incomplete file")
                except ValueError:
                    conn.send(b"ERROR: Invalid file format")
            else:
                broadcast_message(f"{username}: {msg}", conn)

    except (ConnectionResetError, BrokenPipeError, timeout) as e:
        logging.error(f"[!] Connection error with {addr}: {e}")
    except Exception as e:
        logging.error(f"[!] Unexpected error with {addr}: {e}")
    finally:
        with lock:
            for client in clients[:]:
                if client[0] == conn:
                    clients.remove(client)
                    break
        conn.close()
        logging.info(f"[-] Disconnected {addr}")

def start_server():
    try:
        if not (os.path.exists("cert.pem") and os.path.exists("key.pem")):
            raise FileNotFoundError("SSL certificate or key file missing")
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        server_sock.listen()
        logging.info(f"[+] Secure Chat Server running on {HOST}:{PORT}")

        with context.wrap_socket(server_sock, server_side=True) as ssock:
            while True:
                try:
                    client_conn, addr = ssock.accept()
                    threading.Thread(target=handle_client, args=(client_conn, addr), daemon=True).start()
                except KeyboardInterrupt:
                    logging.info("\n[!] Server shutting down.")
                    break
    except Exception as e:
        logging.error(f"[!] Server error: {e}")
    finally:
        server_sock.close()

if __name__ == "__main__":
    start_server()
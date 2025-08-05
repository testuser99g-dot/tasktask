import socket
import threading
import os
from database import init_db, add_or_update_user, set_user_offline, save_message, get_online_users

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

clients = []
usernames = {}
lock = threading.Lock()

def broadcast(message, sender_socket):
    with lock:
        for client in clients[:]:
            if client != sender_socket:
                try:
                    client.sendall(message)
                except Exception as e:
                    print(f"[!] Error sending to {usernames.get(client, 'unknown')}: {e}")
                    client.close()
                    clients.remove(client)

def broadcast_file_to_all(filename, filedata, sender_socket):
    filesize = len(filedata)
    header = f"FILE:{filename}:{filesize}".encode() + b'\n'
    with lock:
        for client in clients[:]:
            if client != sender_socket:
                try:
                    client.setblocking(True)
                    if client.fileno() == -1:
                        print(f"[!] Socket is closed before broadcasting file to {usernames.get(client, 'unknown')}")
                        continue
                    client.sendall(header)
                    client.settimeout(120)
                    ack = client.recv(1024).decode('utf-8', errors='ignore').strip()
                    print(f"[DEBUG] Received ack from {usernames.get(client, 'unknown')}: {ack}")
                    if ack == "READY":
                        client.sendall(filedata)
                        print(f"[DEBUG] Sent {filesize} bytes to {usernames.get(client, 'unknown')}")
                    else:
                        print(f"[DEBUG] Client {usernames.get(client, 'unknown')} rejected file: {ack}")
                except Exception as e:
                    print(f"[!] Error sending file to {usernames.get(client, 'unknown')}: {e}")
                    client.close()
                    clients.remove(client)
                finally:
                    client.settimeout(None)

def handle_client(client_socket, address):
    ip_address, port = address
    try:
        client_socket.sendall(b"Enter your username: ")
        username = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()
        with lock:
            clients.append(client_socket)
            usernames[client_socket] = username
        add_or_update_user(username, ip_address, port)
        print(f"[+] {username} connected from {ip_address}:{port}")

        while True:
            client_socket.settimeout(120)
            if client_socket.fileno() == -1:
                print(f"[!] Socket is closed for {username}")
                break
            # دریافت هدر پیام
            data = client_socket.recv(BUFFER_SIZE).decode('utf-8', errors='ignore').strip()
            if not data:
                raise ConnectionError("No data received")

            if data.lower() == "exit":
                print(f"[-] {username} disconnected.")
                break

            if data.startswith("FILE:"):
                try:
                    parts = data.split(":", 2)
                    if len(parts) != 3:
                        print(f"[!] Invalid file format: {data}")
                        client_socket.send(b"ERROR: Invalid file format\n")
                        continue
                    _, filename, filesize = parts
                    filesize = int(filesize)
                    if filesize > MAX_FILE_SIZE:
                        print(f"[!] File {filename} too large: {filesize} bytes")
                        client_socket.send(b"ERROR: File too large\n")
                        continue
                    print(f"[DEBUG] Sending READY for file {filename}")
                    client_socket.setblocking(True)
                    if client_socket.fileno() == -1:
                        print(f"[!] Socket is closed before sending READY for {username}")
                        continue
                    client_socket.send(b"READY\n")
                    filedata = b''
                    remaining = filesize
                    client_socket.settimeout(120)
                    while remaining > 0:
                        if client_socket.fileno() == -1:
                            print(f"[!] Socket is closed during file transfer for {username}")
                            break
                        chunk = client_socket.recv(min(BUFFER_SIZE, remaining))
                        if not chunk:
                            print(f"[DEBUG] No more data, got {len(filedata)}/{filesize} bytes for {filename}")
                            break
                        filedata += chunk
                        remaining -= len(chunk)
                        print(f"[DEBUG] Received {len(filedata)}/{filesize} bytes for {filename}")
                    if len(filedata) == filesize:
                        print(f"[DEBUG] Successfully received file: {filename} from {username}")
                        # ذخیره نام فایل در دیتابیس
                        online_users = get_online_users()
                        if username in online_users:
                            online_users.remove(username)  # فرستنده جزو گیرندگان نیست
                        save_message(username, f"File: {filename}", online_users)
                        broadcast_file_to_all(filename, filedata, client_socket)
                        client_socket.send(b"FILE_SENT\n")
                        print(f"[FILE] {username} sent {filename}")
                    else:
                        print(f"[!] Incomplete file: {len(filedata)}/{filesize} bytes for {filename}")
                        client_socket.send(b"ERROR: Incomplete file\n")
                except ValueError as e:
                    print(f"[!] Invalid file format: {data}, error: {e}")
                    client_socket.send(b"ERROR: Invalid file format\n")
                except OSError as e:
                    print(f"[!] Socket error during file transfer: {e}")
                    client_socket.send(b"ERROR: Socket issue\n")
                finally:
                    client_socket.settimeout(None)
            else:
                # ذخیره پیام متنی در دیتابیس
                online_users = get_online_users()
                if username in online_users:
                    online_users.remove(username)  # فرستنده جزو گیرندگان نیست
                save_message(username, data, online_users)
                full_msg = f"{username}: {data}".encode() + b'\n'
                broadcast(full_msg, client_socket)

    except Exception as e:
        print(f"[!] Error with {username}: {e}")
    finally:
        set_user_offline(username)
        with lock:
            if client_socket in clients:
                clients.remove(client_socket)
            if client_socket in usernames:
                del usernames[client_socket]
        client_socket.close()
        print(f"[-] {username} disconnected from {ip_address}:{port}")

def start_server():
    try:
        init_db()  # مقداردهی اولیه دیتابیس
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"[+] Chat Server running on {HOST}:{PORT}")
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down.")
    except Exception as e:
        print(f"[!] Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
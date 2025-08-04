import socket
import threading

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096

clients = []
usernames = {}
lock = threading.Lock()

def broadcast(message, sender_socket):
    with lock:
        for client in clients[:]:
            if client != sender_socket:
                try:
                    client.sendall(message)
                except:
                    client.close()
                    clients.remove(client)

def broadcast_file_to_all(filename, filedata, sender_socket):
    filesize = len(filedata)
    header = f"FILE:{filename}:{filesize}".encode() + b'\n'
    with lock:
        for client in clients[:]:
            if client != sender_socket:
                try:
                    client.sendall(header)
                    client.sendall(filedata)
                except Exception as e:
                    print(f"send file to {client}is faild. {e}")
                    client.close()
                    clients.remove(client)

def handle_client(client_socket, address):
    try:
        client_socket.sendall(b"Enter your username: ")
        username = client_socket.recv(1024).decode().strip()
        with lock:
            clients.append(client_socket)
            usernames[client_socket] = username
        print(f"[+] {username} connected from {address}")

        while True:
            data = b''
            while not data.endswith(b'\n'):
                chunk = client_socket.recv(1)
                if not chunk:
                    raise ConnectionError
                data += chunk

            msg = data.decode().strip()
            if msg.lower() == "exit":
                print(f"[-] {username} disconnected.")
                break

            if msg.startswith("FILE:"):
                parts = msg.split(":", 2)
                if len(parts) != 3:
                    continue
                _, filename, filesize = parts
                filesize = int(filesize)

                filedata = b''
                remaining = filesize
                while remaining > 0:
                    chunk = client_socket.recv(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        break
                    filedata += chunk
                    remaining -= len(chunk)

                print(f" {username} sent a file: {filename} ({filesize} bytes)")
                broadcast_file_to_all(filename, filedata, client_socket)
            else:
                full_msg = f"{username}: {msg}".encode() + b'\n'
                broadcast(full_msg, client_socket)

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        with lock:
            if client_socket in clients:
                clients.remove(client_socket)
            if client_socket in usernames:
                del usernames[client_socket]
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f" Server listening on {HOST}:{PORT}")
    try:
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()

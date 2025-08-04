import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096
DOWNLOAD_DIR = "downloads"

def receive_messages(sock):
    while True:
        try:
            data = b''
            while not data.endswith(b'\n'):
                chunk = sock.recv(1)
                if not chunk:
                    raise ConnectionError
                data += chunk
            msg = data.decode().strip()

            if msg.startswith("FILE:"):
                _, filename, filesize = msg.split(":", 2)
                filesize = int(filesize)
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                os.makedirs(DOWNLOAD_DIR, exist_ok=True)
                with open(filepath, "wb") as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = sock.recv(min(BUFFER_SIZE, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                print(f"\n📥 File received and saved as: {filepath}")
            else:
                print("\n" + msg)
        except:
            print("🔌 Connection lost.")
            break

def send_messages(sock):
    while True:
        try:
            msg = input()
            if msg.lower() == "exit":
                sock.sendall(b"exit\n")
                break
            elif msg.startswith("/sendfile "):
                path = msg.split(" ", 1)[1]
                if not os.path.isfile(path):
                    print("File not found.")
                    continue
                filename = os.path.basename(path)
                filesize = os.path.getsize(path)
                header = f"FILE:{filename}:{filesize}\n".encode()
                sock.sendall(header)
                with open(path, "rb") as f:
                    while True:
                        chunk = f.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        sock.sendall(chunk)
                print(f"📤 File {filename} sent to all clients.")
            else:
                sock.sendall(msg.encode() + b'\n')
        except:
            break

def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    prompt = sock.recv(1024).decode()
    username = input(prompt)
    sock.sendall(username.encode() + b'\n')

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
    send_messages(sock)
    sock.close()

if __name__ == "__main__":
    start_client()

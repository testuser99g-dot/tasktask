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
                chunk = sock.recv(BUFFER_SIZE)
                if not chunk:
                    raise ConnectionError("No data received")
                data += chunk
            msg = data.decode('utf-8', errors='ignore').strip()

            if msg.startswith("FILE:"):
                _, filename, filesize = msg.split(":", 2)
                filesize = int(filesize)
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                os.makedirs(DOWNLOAD_DIR, exist_ok=True)
                with open(filepath, "wb") as f:
                    remaining = filesize
                    sock.settimeout(120)
                    while remaining > 0:
                        chunk = sock.recv(min(BUFFER_SIZE, remaining))
                        if not chunk:
                            print(f"[DEBUG] No more data, got {filesize - remaining}/{filesize} bytes for {filename}")
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                        print(f"[DEBUG] Received {filesize - remaining}/{filesize} bytes for {filename}")
                    if remaining == 0:
                        print(f"\n📥 File received and saved as: {filepath}")
                    else:
                        print(f"\n[!] Incomplete file: {filepath}, got {filesize - remaining}/{filesize} bytes")
            elif msg.startswith("ERROR:"):
                print(f"\n[!] Server error: {msg}")
            elif msg == "FILE_SENT":
                print(f"\n[FILE] File successfully sent to server")
            else:
                print("\n" + msg)
        except ConnectionError:
            print("\n🔌 Connection lost.")
            break
        except Exception as e:
            print(f"\n[!] Error receiving: {e}")
            break
        finally:
            sock.settimeout(None)

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
                print(f"[DEBUG] File size of {filename}: {filesize} bytes")
                header = f"FILE:{filename}:{filesize}\n".encode()
                sock.setblocking(True)
                sock.sendall(header)
                sock.settimeout(30)
                ack = sock.recv(BUFFER_SIZE).decode('utf-8', errors='ignore').strip()
                print(f"[DEBUG] Received: {ack}")
                if ack == "READY":
                    with open(path, "rb") as f:
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk:
                                break
                            sock.sendall(chunk)
                    print(f"[DEBUG] Sending file data: {filesize} bytes")
                    sock.settimeout(30)
                    final_ack = sock.recv(BUFFER_SIZE).decode('utf-8', errors='ignore').strip()
                    print(f"[DEBUG] Final server response: {final_ack}")
                    if final_ack == "FILE_SENT":
                        print(f"[FILE] Sent file: {filename}")
                    else:
                        print(f"[!] Server response: {final_ack}")
                else:
                    print(f"[!] Server rejected file: {ack}")
            else:
                sock.sendall(msg.encode() + b'\n')
        except Exception as e:
            print(f"[!] Error sending: {e}")
            break
        finally:
            sock.settimeout(None)

def start_client():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        prompt = sock.recv(BUFFER_SIZE).decode('utf-8', errors='ignore').strip()
        if not prompt.startswith("Enter your username"):
            print("[!] Failed to receive server prompt")
            return
        username = input(prompt)
        sock.sendall(username.encode('utf-8') + b'\n')
        print("[*] Type 'exit' to quit, '/sendfile filename' to send file")
        threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
        send_messages(sock)
    except Exception as e:
        print(f"[!] Connection error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    start_client()
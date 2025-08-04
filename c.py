import socket
import ssl
import threading
import os
from socket import timeout

HOST = '127.0.0.1'
PORT = 12345
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

def receive_messages(sock):
    while True:
        try:
            sock.settimeout(60)  # Timeout for receiving data
            data = sock.recv(1024)
            if not data:
                break
            try:
                msg = data.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                print(f"[!] Invalid data received")
                continue

            if msg.startswith("FILE:"):
                try:
                    _, filename, filesize = msg.split(":")
                    filesize = int(filesize)
                    if filesize > MAX_FILE_SIZE:
                        print("[!] File too large to receive")
                        continue
                    sock.send(b"READY")
                    with open(f"received_{filename}", "wb") as f:
                        received = 0
                        while received < filesize:
                            chunk = sock.recv(min(4096, filesize - received))
                            if not chunk:
                                break
                            f.write(chunk)
                            received += len(chunk)
                        if received == filesize:
                            print(f"[FILE] Received file: received_{filename}")
                        else:
                            print(f"[!] Incomplete file: received_{filename}")
                except ValueError:
                    print("[!] Invalid file format received")
            elif msg.startswith("ERROR:"):
                print(f"[!] Server error: {msg}")
            elif msg == "FILE_SENT":
                print("[FILE] File successfully sent to server")
            else:
                print(msg)
        except (ConnectionResetError, BrokenPipeError, timeout) as e:
            print(f"[!] Connection error: {e}")
            break
        except Exception as e:
            print(f"[!] Unexpected error receiving: {e}")
            break
        finally:
            sock.settimeout(None)

def start_client():
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((HOST, PORT)) as sock:
            with context.wrap_socket(sock, server_hostname=HOST) as ssock:
                # Receive and verify server prompt
                prompt = ssock.recv(1024).decode('utf-8', errors='ignore')
                if not prompt.startswith("Enter your username"):
                    print("[!] Failed to receive server prompt")
                    return

                username = input("Enter your username: ")
                print("[*] Type 'exit' to quit, 'sendfile filename' to send file")
                threading.Thread(target=receive_messages, args=(ssock,), daemon=True).start()
                ssock.send(username.encode('utf-8'))

                while True:
                    msg = input()
                    if msg.lower() == "exit":
                        ssock.send(b"exit")
                        break
                    elif msg.startswith("sendfile "):
                        filename = msg.split(" ", 1)[1]
                        if os.path.exists(filename):
                            file_size = os.path.getsize(filename)
                            if file_size > MAX_FILE_SIZE:
                                print("[!] File too large to send")
                                continue
                            with open(filename, "rb") as f:
                                filedata = f.read()
                            ssock.send(f"FILE:{os.path.basename(filename)}:{len(filedata)}".encode('utf-8'))
                            ssock.settimeout(5)  # Timeout for receiving READY
                            ack = ssock.recv(1024).decode('utf-8', errors='ignore')
                            if ack == "READY":
                                ssock.sendall(filedata)
                                print(f"[FILE] Sent file: {filename}")
                            else:
                                print(f"[!] Server rejected file: {ack}")
                            ssock.settimeout(None)
                        else:
                            print("[!] File not found.")
                    else:
                        ssock.send(msg.encode('utf-8'))
    except (ConnectionResetError, BrokenPipeError, timeout) as e:
        print(f"[!] Connection error: {e}")
    except Exception as e:
        print(f"[!] Unexpected error: {e}")

if __name__ == "__main__":
    start_client()

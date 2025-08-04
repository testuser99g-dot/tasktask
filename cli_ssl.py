import socket
import ssl
import threading
import os

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            msg = data.decode()

            if msg.startswith("FILE:"):
                _, filename, filesize = msg.split(":")
                filesize = int(filesize)
                sock.send(b"READY")
                with open(f"received_{filename}", "wb") as f:
                    received = 0
                    while received < filesize:
                        chunk = sock.recv(min(4096, filesize - received))
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)
                print(f"[FILE] Received file: received_{filename}")
            else:
                print(msg)
        except Exception as e:
            print(f"[!] Error receiving: {e}")
            break

def start_client():
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((HOST, PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=HOST) as ssock:
            username = input("Enter your username: ")
            print("[*] Type 'exit' to quit, 'sendfile filename' to send file")
            threading.Thread(target=receive_messages, args=(ssock,), daemon=True).start()
            ssock.recv(1024)  # Prompt from server
            ssock.send(username.encode())

            while True:
                msg = input()
                if msg.lower() == "exit":
                    ssock.send(b"exit")
                    break
                elif msg.startswith("sendfile "):
                    filename = msg.split(" ", 1)[1]
                    if os.path.exists(filename):
                        with open(filename, "rb") as f:
                            filedata = f.read()
                        ssock.send(f"FILE:{os.path.basename(filename)}:{len(filedata)}".encode())
                        ack = ssock.recv(1024)
                        if ack == b"READY":
                            ssock.sendall(filedata)
                        print(f"[FILE] Sent file: {filename}")
                    else:
                        print("[!] File not found.")
                else:
                    ssock.send(msg.encode())

if __name__ == "__main__":
    start_client()

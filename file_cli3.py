import socket
import threading
import os
from socket import timeout

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

def receive_messages(sock):
    while True:
        try:
            sock.settimeout(600)
            if sock.fileno() == -1:
                print("[!] Socket is closed")
                break
            data = b''
            while not data.endswith(b'\n'):
                chunk = sock.recv(1)
                if not chunk:
                    print("[DEBUG] No data received, closing socket")
                    break
                data += chunk
            if not data:
                break

            try:
                msg = data.decode('utf-8', errors='ignore').strip()
            except UnicodeDecodeError:
                print(f"[!] Invalid data received")
                continue

            if msg.startswith("FILE:"):
                try:
                    _, filename, filesize = msg.split(":", 2)
                    filesize = int(filesize)
                    print(f"[DEBUG] Expecting file {filename} with size {filesize} bytes")
                    if filesize > MAX_FILE_SIZE:
                        print("[!] File too large to receive")
                        continue
                    sock.setblocking(True)
                    sock.send(b"READY\n")
                    with open(f"received_{filename}", "wb") as f:
                        received = 0
                        while received < filesize:
                            if sock.fileno() == -1:
                                print("[!] Socket is closed during file transfer")
                                break
                            chunk = sock.recv(min(BUFFER_SIZE, filesize - received))
                            if not chunk:
                                print(f"[DEBUG] No more data, got {received}/{filesize} bytes")
                                break
                            f.write(chunk)
                            received += len(chunk)
                            print(f"[DEBUG] Received {received}/{filesize} bytes")
                        if received == filesize:
                            print(f"[FILE] Received file: received_{filename}")
                        else:
                            print(f"[!] Incomplete file: received_{filename}, got {received}/{filesize} bytes")
                except ValueError as e:
                    print(f"[DEBUG] Invalid file format: {msg}, error: {e}")
                except OSError as e:
                    print(f"[!] Socket error during file receive: {e}")
                    break
            elif msg.startswith("ERROR:"):
                print(f"[!] Server error: {msg}")
            elif msg == "FILE_SENT":
                print("[FILE] File successfully sent to server")
            else:
                print(msg)
        except (ConnectionResetError, BrokenPipeError, timeout) as e:
            print(f"[!] Connection error: {e}")
            break
        except OSError as e:
            print(f"[!] Socket error: {e}")
            break
        except Exception as e:
            print(f"[!] Unexpected error receiving: {e}")
            break
        finally:
            sock.settimeout(None)

def start_client():
    try:
        with socket.create_connection((HOST, PORT)) as sock:
            sock.setblocking(True)
            prompt = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            if not prompt.startswith("Enter your username"):
                print("[!] Failed to receive server prompt")
                return

            username = input("Enter your username: ")
            print("[*] Type 'exit' to quit, 'sendfile filename' to send file")
            threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
            sock.send(username.encode('utf-8') + b'\n')

            while True:
                msg = input()
                if msg.lower() == "exit":
                    sock.send(b"exit\n")
                    break
                elif msg.startswith("sendfile "):
                    filename = msg.split(" ", 1)[1]
                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        print(f"[DEBUG] File size of {filename}: {file_size} bytes")
                        if file_size > MAX_FILE_SIZE:
                            print(f"[!] File too large to send ({file_size} bytes, max {MAX_FILE_SIZE} bytes)")
                            continue
                        with open(filename, "rb") as f:
                            filedata = f.read()
                        try:
                            print(f"[DEBUG] Sending FILE:{os.path.basename(filename)}:{len(filedata)}")
                            sock.setblocking(True)
                            if sock.fileno() == -1:
                                print("[!] Socket is closed before sending file")
                                continue
                            sock.send(f"FILE:{os.path.basename(filename)}:{len(filedata)}\n".encode('utf-8'))
                            sock.settimeout(30)
                            ack = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                            print(f"[DEBUG] Received: {ack}")
                            if ack == "READY":
                                print(f"[DEBUG] Sending file data: {len(filedata)} bytes")
                                sock.sendall(filedata)
                                print(f"[FILE] Sent file: {filename}")
                                sock.settimeout(30)
                                final_ack = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                                print(f"[DEBUG] Final server response: {final_ack}")
                            else:
                                print(f"[!] Server rejected file with reason: {ack}")
                        except OSError as e:
                            print(f"[!] Socket error: {e}")
                        except Exception as e:
                            print(f"[!] Unexpected error during file transfer: {e}")
                        finally:
                            sock.settimeout(None)
                    else:
                        print("[!] File not found.")
                else:
                    sock.send(f"{msg}\n".encode('utf-8'))
    except (ConnectionResetError, BrokenPipeError, timeout) as e:
        print(f"[!] Connection error: {e}")
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
    finally:
        try:
            sock.close()
            print("[DEBUG] Socket closed")
        except NameError:
            pass

if __name__ == "__main__":
    start_client()
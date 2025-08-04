import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

clients = []
usernames = {}
lock = threading.Lock()

def broadcast(message, sender_socket=None):
    with lock:
        for client in clients[:]:  # کپی برای جلوگیری از تغییر همزمان
            if client != sender_socket:
                try:
                    client.sendall(message)
                except Exception as e:
                    print(f"error to send msg: {e}")
                    client.close()
                    clients.remove(client)
                    if client in usernames:
                        del usernames[client]

def handle_client(client_socket, address):
    print(f"new: {address}")
    try:
        # ارسال درخواست یوزرنیم به کلاینت
        client_socket.sendall("enter your username:  ".encode())
        username = client_socket.recv(1024).decode().strip()
        if not username:
            client_socket.close()
            return

        with lock:
            clients.append(client_socket)
            usernames[client_socket] = username

        print(f" {username}enter to chat")
        broadcast(f"{username}enter to chat\n".encode(), client_socket)

        # دریافت پیام‌ها
        while True:
            message = client_socket.recv(1024)
            if not message:
                break

            decoded = message.decode().strip()
            if decoded.lower() == 'exit':
                break

            full_message = f"[{username}]: {decoded}".encode()
            broadcast(full_message, client_socket)

    except Exception as e:
        print(f"erroer to connection {address}: {e}")

    finally:
        with lock:
            if client_socket in clients:
                clients.remove(client_socket)
            if client_socket in usernames:
                username = usernames[client_socket]
                del usernames[client_socket]
                broadcast(f"{username}leave the chat \n".encode(), client_socket)

        client_socket.close()
        print(f"connection clossed with {address}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"server running on {HOST}:{PORT}")

    try:
        while True:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\nclossed connection with ctrl+c")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()

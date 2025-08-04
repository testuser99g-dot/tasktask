import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(conn):
    while True:
        try:
            message = conn.recv(1024).decode()
            if message.lower() == 'exit':
                print("client leave the chat.")
                break
            print(f"\nclient: {message}")
        except:
            break
    conn.close()

def send_messages(conn):
    try:
        while True:
            msg = input("you: ")
            conn.sendall(msg.encode())
            if msg.lower() == 'exit':
                break
    except KeyboardInterrupt:
        print("\nchat clossed by client")
    conn.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Connected to server at{HOST}:{PORT}")
conn, addr = server_socket.accept()
print(f"client connected by: {addr}")

t1 = threading.Thread(target=receive_messages, args=(conn,))
t2 = threading.Thread(target=send_messages, args=(conn,))

t1.start()
t2.start()

t1.join()
t2.join()

server_socket.close()
print("server turnoff")

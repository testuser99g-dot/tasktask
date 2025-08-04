import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if message.lower() == 'exit':
                print("server leave the chat.")
                break
            print(f"\nserver: {message}")
        except:
            break
    sock.close()

def send_messages(sock):
    try:
        while True:
            msg = input("you ")
            sock.sendall(msg.encode())
            if msg.lower() == 'exit':
                break
    except KeyboardInterrupt:
        print("\n clossed by client")
    sock.close()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((HOST, PORT))
    print("connected")
except:
    print("connection faild")
    exit()

t1 = threading.Thread(target=receive_messages, args=(client_socket,))
t2 = threading.Thread(target=send_messages, args=(client_socket,))

t1.start()
t2.start()

t1.join()
t2.join()

print("connection clossed")

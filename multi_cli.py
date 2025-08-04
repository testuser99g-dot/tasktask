import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024)
            if not message:
                print("server connection is done")
                break
            print(message.decode())
        except:
            print("error to recv msg")
            break

def send_messages(sock):
    while True:
        try:
            msg = input()
            if msg.strip().lower() == 'exit':
                sock.sendall(msg.encode())
                break
            sock.sendall(msg.encode())
        except:
            print("error to send msg")
            break

def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))

        # دریافت پیام "لطفاً یوزرنیم وارد کنید"
        prompt = client.recv(1024).decode()
        print(prompt, end='')

        # ارسال یوزرنیم به سرور
        username = input()
        client.sendall(username.encode())

        # شروع threadها برای ارسال و دریافت
        recv_thread = threading.Thread(target=receive_messages, args=(client,))
        send_thread = threading.Thread(target=send_messages, args=(client,))
        recv_thread.start()
        send_thread.start()

        # منتظر پایان یکی از threadها بمون
        send_thread.join()
    except KeyboardInterrupt:
        print("\n leave with Ctrl+C")
    except Exception as e:
        print(f"error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_client()

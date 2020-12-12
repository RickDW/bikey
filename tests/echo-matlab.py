import socket
import time

HOST = "127.0.0.1" # standard loopback interface address (localhost)
PORT = 65432       # Port to listen on (non-priviliged ports are > 1023)

# specify address family and socket type
# address family = socket.AF_INET -> IPv4
# socket type = socket.SOCK_STREAM -> TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    x = 0
    started = False

    while x < 100:
        conn, addr = s.accept()
        if not started:
            start_time = time.time()
            started = True

        with conn:
            data = conn.recv(1024)
            conn.sendall(str(x).encode('utf-8') + b'\n')
            x += 1

duration = time.time() - start_time
print(f"{x} messages have been sent in {duration} seconds.")
print("Server has shutdown")
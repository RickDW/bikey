import socket

HOST = "127.0.0.1" # standard loopback interface address (localhost)
PORT = 65432       # Port to listen on (non-priviliged ports are > 1023)

# specify address family and socket type
# address family = socket.AF_INET -> IPv4
# socket type = socket.SOCK_STREAM -> TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()

    with conn:
        print("Connected by", addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)

print("Server has shutdown")
import matlab.engine
import bikey.utils
import socket

engine = matlab.engine.start_matlab('-desktop')
engine.cd(bikey.utils.find_template_dir(), nargout = 0)

model = 'inputtest'
handle = engine.open_system(model, nargout = 0)
print("Matlab loaded")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 0))
server.listen()
port = server.getsockname()[1]
print(f"Server socket listening on port {port}")

engine.set_param(f'{model}/server port', 'value', str(port), nargout = 0)
print("Provided simulink model with port number")

connection, address = server.accept()
while True:
    data = connection.recv(1024)
    if not data:
        break

    connection.sendall('129\n'.encode('utf-8'))

server.close()
print("Server socket closed")
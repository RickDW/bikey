import socket
import json
import argparse
import time


_delimiter = b'<END>'
_encoding = 'utf-8'


def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        description='Shut down a running RL environment server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-H', '--host',
                        help = 'the host on which the server can be reached',
                        default = '127.0.0.1')
    parser.add_argument('-p', '--port',
                        help = 'the port on which the server is listening',
                        default = 65432,
                        type = int)

    args = parser.parse_args()

    return args.host, args.port


def send_shutdown_command(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))

            message = json.dumps({'command': 'shut_down_server'})

            s.sendall(message.encode(_encoding) + _delimiter)

            data = s.recv(1024)

            if not data:
                # connection is broken, as expected
                print("Connection is broken as expected")

            else:
                print("Error: server has sent a message instead of shutting down")

    except ConnectionRefusedError:
        print("Could not connect to server")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # the main server thread could be blocking due to a call to accept()
            # by connecting one more time it snaps out of this, but due to the
            # stop_server Event being set it will not go back to blocking with
            # accept() ==> it shuts down
            s.connect((host, port))
            print("Ding dong ditching the server")

    except ConnectionRefusedError:
        print("Second connection was broken, server must already be shut down")

    print("Server should be shut down soon")


def main():
    host, port = parse_cli_arguments()
    send_shutdown_command(host, port)


if __name__ == '__main__':
    main()
import socket
import json
import argparse


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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        message = json.dumps({'command': 'shut_down_server'})

        s.sendall(message.encode(_encoding) + _delimiter)

        data = s.recv(1024)

        if not data:
            # connection is broken, as expected
            print("Server has shut down")

        else:
            print("Error: server has sent a message instead of shutting down")


def main():
    host, port = parse_cli_arguments()
    send_shutdown_command(host, port)


if __name__ == '__main__':
    main()
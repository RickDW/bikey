import json
import socket
import time
import multiprocessing as mp
import threading

from . import server_utils
from .env_process import run_environment


_delimiter = b'<END>'
_encoding = 'utf-8'


def start_server(host, port, server_dir, max_connections):
    """
    Start an environment server on the specified interface and port.

    As long as the number of connections is below the connections limit,
    any incoming connections will be accepted. Each connection is given a
    separate thread, and a process in which the environment can execute
    unimpeded. This way, any CPU-bound computations do not block the server's
    connections either.

    Arguments:
    host -- The interface to listen on
    port -- The port to listen on
    server_dir -- The directory where the server can store its files (this is
        only used with SpacarEnv's)
    max_connections -- The maximum number of simultaneous connections. This is
        useful when one environment takes up a lot of resources, for example,
        and having too many executing simultaneously would impact performance.
    """
    connections = []

    dir_thread, stop_dir_generator, name_queue = server_utils.setup_name_queue(server_dir)
    stop_server = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()

        while not stop_server.is_set():
            # don't keep track of closed connections
            connections = [(a, t) for a, t in connections if t.is_alive()]

            # display all connections
            server_utils.display_connections(connections)

            if len(connections) <= max_connections:
                print("Waiting for new connection")
                client_socket, addr = s.accept()

                print("Incoming connection from: ", addr)

                # determine if the client is running on this machine as well
                from_server = host == addr[0]

                thread = threading.Thread(target=handle_client,
                                          args=(client_socket, from_server,
                                                stop_server, name_queue))
                connections.append((addr, thread))
                thread.start()

            else:
                print('Server full')
                print('Waiting 30 seconds before checking available slots again')
                time.sleep(10)  # wait a little before checking again

    # stop the thread that generates working directories
    stop_dir_generator.set()

    # if all goes well all threads will exit and the server shutdown message
    # is displayed

    for address, thread in connections:
        thread.join()
        print("One thread is definitely dead")

    dir_thread.join()
    print("Directory gen. thread is definitely dead")

    # shutdown message is only displayed if all threads have died
    print("Environment server has shutdown")
    print("All threads or processes are dead")


def handle_client(client_socket, from_server, stop_server, name_queue):
    """
    Handles all communications with clients of the server in its own thread.

    Arguments:
    client_socket -- The socket associated with the connection.
    stop_server -- A threading.Event that stops the entire server when set
    name_queue - A multiprocessing.Queue object containing designated
        directories for clients
    """
    # print('Created a new thread')
    read_buffer = b''

    message_queue = mp.Queue()
    response_queue = mp.Queue()

    env_process = mp.Process(
        target=run_environment,
        args=(message_queue, response_queue, name_queue))

    env_process.start()

    try:
        with client_socket:
            while not stop_server.is_set():
                # print('Waiting for a new message')

                data = client_socket.recv(1024)

                if not data:
                    # connection is broken, shut down everything
                    message_queue.put(None)
                    break

                read_buffer += data

                if _delimiter in read_buffer:
                    # a full message has been received, put it in the queue
                    raw_message, read_buffer = \
                        read_buffer.split(_delimiter, maxsplit=1)
                    message = json.loads(raw_message.decode(_encoding))
                    # make sure observations are turned into numpy arrays
                    server_utils.numpyify(message)
                    # print('Received new message: ', message)

                    message_queue.put(message)

                    # wait for a response from the process
                    response = response_queue.get()

                    # print('Received response from process: ', response)

                    if response is None:
                        if from_server:
                            # the entire server should be shut down (requested
                            # by client)
                            print("Request from same machine")
                            stop_server.set()
                            print("Server-wide shutdown initiated")

                        break

                    # make sure observations are turned into lists before being
                    # turned into json
                    server_utils.denumpyify(response)
                    client_socket.sendall(
                        json.dumps(response).encode(_encoding) + _delimiter)

                    # print('Sent process response to client')

            else:
                # the stop_server event was set
                message_queue.put(None)

    except ConnectionResetError:
        # print("The connection with the client was broken, killing thread and process")
        message_queue.put(None)

    # print("End of thread")
    env_process.join()
    # print("End of process")


def main():
    args = server_utils.parse_cli_args()

    print("The environment server that is being accessed is specified as:")
    print(f"\t- Host: {args.host}")
    print(f"\t- Port: {args.port}")
    print()

    if args.stop:
        print("This server will now be shut down.")
        server_utils.send_shutdown_command(args.host, args.port)

    else:
        print("An environment server will be started with the following properties:\n")
        print(f"\t- Directory: {args.directory}")
        print(f"\t- Max. connections: {args.max_connections}")

        start_server(args.host, args.port, args.directory, args.max_connections)

    print("End of server.py")


if __name__ == '__main__':
    main()

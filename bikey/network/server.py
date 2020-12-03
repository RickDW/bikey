import gym
import bikey
import numpy as np
import socket
import json
import multiprocessing as mp
import threading
from time import sleep


_delimiter = b'<END>'
_encoding = 'utf-8'

HOST = "127.0.0.1"
PORT = 65432
max_connections = 10

server_dir = 'C:\\Users\\Rick\\Museum\\bikey\\tests' # restricted access


def start_server(host, port):
    """
    Start an environment server on the specified interface and port.

    As long as the number of connections is below the max_connections limit,
    any incoming connections will be given their own thread. These threads in
    turn will spawn a process that will run the environment. This way any
    CPU-bound computations do not block the server's connections.

    Arguments:
    host -- The interface to listen on
    port -- The port to listen on
    """
    threads = []
    connection_count = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            threads = [(a, t) for a, t in threads if t.is_alive()]
            connection_count = len(threads)

            # display all connections
            print('\n' + '-' * 40)
            if len(threads) > 0:
                print("Current connections:")
                for i, (address, thread) in enumerate(threads):
                    print(f"Connection {i} :: address {address}")
            else:
                print("Currently not connected to any clients")
            print('\n' + '-' * 40 + '\n')

            if connection_count <= max_connections:
                print("Waiting for new connection")
                client_socket, addr = s.accept()

                print("Incoming connection from: ", addr)
                thread = threading.Thread(target = handle_client,
                                          args = (client_socket,))
                threads.append((addr, thread))
                thread.start()
                connection_count += 1

            else:
                print('Server full')
                print('Waiting 30 seconds before checking available slots again')
                sleep(30) # wait half a minute before checking again

    for address, thread in threads:
        thread.join()

    print("Environment server has shutdown.")


def handle_client(client_socket):
    """
    Handles all communications with clients of the server in its own thread.

    Arguments:
    client_socket -- The socket associated with the connection.
    """
    print('Created a new thread')
    read_buffer = b''

    message_queue = mp.Queue()
    response_queue = mp.Queue()

    process = mp.Process(target=run_environment,
                      args=(message_queue, response_queue))

    process.start()

    try:
        with client_socket:
            while True:
                print('Waiting for a new message')

                data = client_socket.recv(1024)

                if not data:
                    # connection is broken, shutdown everything
                    message_queue.put({'command': 'close'})
                    break

                read_buffer += data

                if _delimiter in read_buffer:
                    # a full message has been received, put it in the queue
                    raw_message, read_buffer = \
                        read_buffer.split(_delimiter, maxsplit=1)
                    message = json.loads(raw_message.decode(_encoding))
                    # make sure observations are turned into numpy arrays
                    numpyify(message)
                    print('Received new message: ', message)
                    message_queue.put(message)

                    # wait for a response from the process
                    response = response_queue.get()

                    print('Received response from process: ', response)

                    if response is None:
                        # process will die
                        # break out of the loop, this will close the client socket
                        # process.join() shouldn't block since it's dead
                        # and then the thread will die too, freeing up a connection
                        break

                    # make sure observations are turned into lists before being
                    # turned into json
                    denumpyify(response)
                    client_socket.sendall(
                        json.dumps(response).encode(_encoding) + _delimiter)

                    print('Sent process response to client')

    except ConnectionResetError:
        print("The connection with the client was broken, killing thread and process")
        message_queue.put({'command': 'close'})

    print("End of thread")
    process.join()
    print("End of process")


def numpyify(message):
    """
    Transforms specified 'action' into a numpy array.

    At this point the numpy array is stored in its .tolist() form.

    Arguments:
    message -- The message stored in a python dictionary
    """
    if 'data' in message and 'action' in message['data']:
        message['data']['action'] = \
            np.array(message['data']['action'])


def denumpyify(message):
    """
    Transforms 'observation' numpy array into list form.

    Replaces the 'observation' with its array.tolist() form.

    Arguments:
    message -- The message stored in a python dictionary
    """
    if 'data' in message and 'observation' in message['data']:
        message['data']['observation'] = \
            message['data']['observation'].tolist()


def run_environment(message_queue, response_queue):
    """
    Makes requested calls to an environment.

    The code in this function will always run in its own process, so CPU-bound
    code does not block the server. Queues are used to communicate with the
    server.

    Arguments:
    message_queue -- Any requests will come in through this queue
    response_queue -- Once a request is done, a confirmation needs to be put in
        this queue.
    """
    print("Initialized new process")
    initialized = False
    reset = False

    while True:
        # process incoming messages
        message = message_queue.get()
        command = message['command']

        if command == 'init':
            if initialized:
                # TODO already initialized, command inappropriate
                continue

            data = message['data']

            if data['env'] == 'BicycleEnv-v0':
                if 'config' in data and 'working_dir' in data['config']:
                    # set working dir to the one that's allowed on the server
                    # TODO: maybe add a check whether the specified dir is a
                    # subdirectory of a server dir?
                    data['config']['working_dir'] = server_dir

            env = gym.make(data['env'], **data['config'])
            initialized = True
            print("Initialized environment")
            response_queue.put({
                'command': 'confirm'
            })

        elif command == 'reset':
            if not initialized:
                # TODO not yet initialized, command inappropriate
                continue

            observation = env.reset()
            reset = True

            print('Reset the environment')

            response_queue.put({
                'command': 'confirm',
                'data': {
                    'observation': observation
                }
            })

        elif command == 'step':
            if not reset:
                # TODO not yet reset, command inappropriate
                continue

            action = message['data']['action']
            observation, reward, done, info = env.step(action)

            response_queue.put({
                'command': 'confirm',
                'data': {
                    'observation': observation,
                    'reward': reward,
                    'done': done,
                    'info': info
                }
            })

        elif command == 'close':
            if initialized:
                env.close()

            response_queue.put(None) # send a sentinel object to notify thread
            # of the end of this process

            break # break out of the loop and let the process die

        else:
            # TODO unsupported command, raise error
            # do not forget to put an item on the response queue, or the thread
            # will block, and so will everything else
            pass


if __name__ == '__main__':
    start_server('127.0.0.1', 65432)

    print("End of server.py")
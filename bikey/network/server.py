import gym
import bikey.bicycle  # registers the env with gym
import numpy as np
import socket
import json
import multiprocessing as mp
import threading
from time import sleep
import datetime
import os


_delimiter = b'<END>'
_encoding = 'utf-8'

HOST = "127.0.0.1"
PORT = 65432
max_connections = 10
server_dir = os.getcwd()


def start_server(host, port, server_dir):
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

    dir_thread, stop_event, name_queue = setup_name_queue(server_dir)

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
                                          args = (client_socket, name_queue))
                threads.append((addr, thread))
                thread.start()
                connection_count += 1

            else:
                print('Server full')
                print('Waiting 30 seconds before checking available slots again')
                sleep(30) # wait half a minute before checking again

    # stop the thread that generates working directories
    stop_event.set()

    dir_thread.join()

    for address, thread in threads:
        thread.join()

    print("Environment server has shutdown")
    print("All threads or processes are dead")


def handle_client(client_socket, name_queue):
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
                      args=(message_queue, response_queue, name_queue))

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


def run_environment(message_queue, response_queue, name_queue):
    """
    Makes requested calls to an environment.

    The code in this function will always run in its own process, so CPU-bound
    code does not block the server. Queues are used to communicate with the
    server.

    Arguments:
    message_queue -- Any requests will come in through this queue
    response_queue -- Once a request is done, a confirmation needs to be put in
        this queue.
    name_queue -- A queue that provides working directories to supported
        environments. Currently only used for BicycleEnv-v0.
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
                # TODO make this env ID check future proof for new versions
                name = name_queue.get()
                if 'config' in data:
                    data['config']['working_dir'] = name
                else:
                    data['config'] = {'working_dir': name}

                # only a name has been generated, now create the directory
                os.makedirs(name)

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


def setup_name_queue(server_dir):
    """
    Creates a fixed size queue that will store possible working directories.

    Returns:
    A three-tuple containing
    - the thread that generates names of working directories
    - a threading.Event instance which allows you to stop the working directory
        generation thread
    - a multiprocessing.Queue instance from which processes can take a working
        directory for their environment, if needed
    """
    name_queue = mp.Queue(maxsize=5)
    stop_event = threading.Event()

    thread = threading.Thread(target=provide_names,
                              args=(server_dir, name_queue, stop_event))

    thread.start()

    return thread, stop_event, name_queue


def provide_names(base_dir, queue, stop_event):
    """
    Keeps adding names to the queue until stop_event is set.

    The names are formatted as follows:
    base_dir/hour.minute-day.month.year-0001, with the date and time
    representing the moment the server started running. This format allows for
    ten thousand directories per server active server, but this still means
    it is not a feasible option for running an environment server without
    stopping.

    The provided queue should have a maximum size, or the thread in which
    this function is called will keep adding subdirectories forever.

    Arguments:
    base_dir -- The directory where the working directories will be located
    queue -- A multiprocessing.Queue instance with a given maximum size
    stop_event -- The event that tells this function to stop producing names
    """
    time_string = datetime.datetime.today().strftime('%H.%M-%d.%m.%Y')
    base = os.path.join(base_dir, time_string + '-')
    counter = 1

    while not stop_event.is_set():
        # keep providing available directory names while thread is alive
        name = base + f'{counter:04}'
        queue.put(name)
        print(f"Put {name} on the queue")
        counter += 1


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


if __name__ == '__main__':
    start_server('127.0.0.1', 65432, server_dir)

    print("End of server.py")
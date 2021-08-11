import multiprocessing as mp
import threading
from queue import Full

import socket
import numpy as np
import datetime
import os
import argparse
import time
import json

import gym

_delimiter = b'<END>'
_encoding = 'utf-8'


def parse_cli_args(host='127.0.0.1', port=65432, directory=os.getcwd(),
                   max_connections=10):
    """
    Parse CLI arguments used to manage an environment server.

    Arguments:
    host -- The default host interface of the server.
    port -- The default port of the server.
    directory -- The default server directory.
    max_connections -- The default maximum number of simultaneous connections.
    """
    parser = argparse.ArgumentParser(
        description='Start or stop an environment server.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-s', '--stop',
                        help='if specified, it will shut down the server instead of starting it',
                        action='store_true')
    parser.add_argument('-H', '--host',
                        help='the host address of the server',
                        default=host)
    parser.add_argument('-p', '--port',
                        help='the port of the server',
                        default=port,
                        type=int)
    parser.add_argument('-d', '--directory',
                        help='the directory where the server will \
                                    store any files',
                        default=directory)
    parser.add_argument('-c', '--max_connections',
                        help='the maximum number of simultaneous connections',
                        default=max_connections,
                        type=int)

    args = parser.parse_args()

    return args


def send_shutdown_command(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))

            message = json.dumps({'command': 'shut_down_server'})

            s.sendall(message.encode(_encoding) + _delimiter)

            data = s.recv(1024)

            if not data:
                # connection is broken, as expected
                print("Connection was broken as expected")

            else:
                print("Error: server has sent a message instead of disconnecting")

    except ConnectionRefusedError:
        print("Could not connect to server")
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # the main server thread could be blocking due to a call to accept()
            # by connecting one more time it snaps out of this, but due to the
            # stop_server Event being set it will not go back to blocking with
            # accept() ==> it shuts down
            s.connect((host, port))
            print("Ding dong ditching the server")

    except ConnectionRefusedError:
        print("Connection could not be established, server must already have \
              shut down")
        return

    print("Server should have shut down soon")


def display_connections(connections):
    """
    Prints all provided connections.

    Arguments:
    connections -- A list of (address, thread) tuples.
    """
    print('\n' + '-' * 40 + '\n')
    if len(connections) > 0:
        print("Current connections:")
        for i, (address, thread) in enumerate(connections):
            print(f"Connection {i} :: address {address}")
    else:
        print("Currently not connected to any clients")
    print('\n' + '-' * 40 + '\n')


def setup_name_queue(server_dir):
    """
    Creates a fixed size queue that will store possible working directories.

    Arguments:
    # TODO

    Returns:
    A three-tuple containing
    - the thread that generates names of working directories
    - a threading.Event instance which allows you to stop the working directory
        generation thread
    - a multiprocessing.Queue instance from which processes can take a working
        directory for their environment, if needed
    """
    N = 10
    name_queue = mp.Queue(maxsize=N)
    stop_dir_generator = threading.Event()

    thread = threading.Thread(target=provide_names,
                              args=(server_dir, name_queue, N,
                                    stop_dir_generator))

    thread.start()

    return thread, stop_dir_generator, name_queue


def provide_names(base_dir, queue, queue_size, stop_dir_generator):
    """
    Keeps adding names to the queue until stop_event is set.

    The names are formatted as follows:
    base_dir/hour.minute-day.month.year-0001, with the date and time
    representing the moment the server started running. This format allows for
    ten thousand directories per server active server, but this still means
    it is not a feasible option for running an environment server without
    ever stopping.

    The provided queue should have a maximum size, or the thread in which
    this function is called will keep adding subdirectories forever.

    Arguments:
    base_dir -- The directory where the working directories will be located.
    queue -- A multiprocessing.Queue instance with a given maximum size.
    queue-size -- The maximum size of the queue
    stop_dir_generator -- The threading.Event that tells this function to stop
        producing directory names.
    """
    time_string = datetime.datetime.today().strftime('%H.%M-%d.%m.%Y')
    base = os.path.join(base_dir, time_string + '-')
    counter = 1

    name = lambda: base + f'{counter:04}'

    # fill up the queue at startup without any delays since it is likely that a
    # series of environments will be started simultaneously
    for i in range(queue_size):
        queue.put(name())
        counter += 1

    while not stop_dir_generator.is_set():
        # keep providing available directory names
        try:
            queue.put(name(), False)  # do not block
        except Full:
            # queue is full, wait a while before trying again
            time.sleep(10)
            continue
        # print(f"Put {name} on the queue")
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


def gym_space_to_dict(space):
    """
    Writes the properties of an observation or action space to a dictionary.

    This can be sent across a network using JSON, to allow the space to be
    reconstructed on a different machine. For now this method only supports
    gym.spaces.Box and gym.spaces.Discrete.

    Arguments:
    space -- The observation or action space to be described.

    Returns:
    A dictionary containing properties of a gym space, i.e. the type of space,
    upper and lower bounds, shape, and data type.
    """
    if type(space) is gym.spaces.Box:
        return {
            'space': 'gym.spaces.Box',
            'low': space.low.tolist(),
            'high': space.high.tolist(),
            'shape': space.shape,
            'dtype': str(space.dtype)
        }
    elif type(space) is gym.spaces.Discrete:
        return {
            'space': 'gym.spaces.Discrete',
            'n': space.n
        }
    else:
        # not supported
        raise TypeError("Cannot convert anything but the gym.spaces.Box space\
                        to JSON")


def dict_to_gym_space(description):
    """
    Reconstruct an observation or action space based on a description.

    Currently only gym.spaces.Box and gym.spaces.Discrete are supported.

    Arguments:
    description -- A dictionary with the following attributes:
        - space: e.g. 'gym.spaces.Box'
        - low and high: the original space's low and high attributes
        converted using np_array.tolist())
        - shape: the shape property of the original space
        - dtype: the data type of the original space

    Returns:
    An object that can be used as the observation or action space of an env
    """
    if description['space'] == 'gym.spaces.Box':
        return gym.spaces.Box(
            low=np.array(description['low']),
            high=np.array(description['high']),
            shape=description['shape'],
            dtype=description['dtype']
        )

    elif description['space'] == 'gym.spaces.Discrete':
        return gym.spaces.Discrete(description['n'])

    else:
        raise TypeError(f"NetworkEnv only supports gym.spaces.Box, not\
                        '{description['space']}'")
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
max_connections = 10

HOST = "127.0.0.1"
PORT = 65432


def start_server(host, port):
    thread_list = []
    connection_count = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            if connection_count <= max_connections:
                print("Waiting for new connection")
                client_socket, addr = s.accept()

                print("Incoming connection from: ", addr)
                thread = threading.Thread(target = handle_client,
                                          args = (client_socket,))
                thread_list.append(thread)
                thread.start()
                connection_count += 1

            else:
                thread_list = [t for t in thread_list if t.is_alive()]
                connection_count = len(thread_list)
                if connection_count <= max_connections:
                    continue  # new connections are welcome
                else:
                    print('Waiting 30 seconds before checking available slots again')
                    sleep(30) # wait half a minute before checking again

    for thread in thread_list:
        thread.join()

    print("Environment server has shutdown.")


def handle_client(client_socket):
    print('Created a new thread')
    read_buffer = b''

    message_queue = mp.Queue()
    response_queue = mp.Queue()

    process = mp.Process(target=run_environment,
                      args=(message_queue, response_queue))

    process.start()

    with client_socket:
        while True:
            print('Waiting for a new message')
            data = client_socket.recv(1024)
            if not data:
                message_queue.put({'command': 'close'})
                response = response_queue.get()

                if response is not None:
                    # TODO this should not happen at all
                    print('Requested end of env process.')
                    print('Did not get sentinel object.')
                    break

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
                    # this breaks out of the loop, closing the client socket
                    # the process.join() shouldn't block since it's dead
                    # and then the thread will die too, freeing up a connection

                    # tell the process to close its environment
                    message_queue.put({'command': 'close'})
                    break

                # make sure observations are turned into lists before being
                # turned into json
                denumpyify(response)
                client_socket.sendall(
                    json.dumps(response).encode(_encoding) + _delimiter)

                print('Sent process response to client')

    print("End of thread")
    process.join()
    print("End of process")


def numpyify(message):
    if 'data' in message and 'action' in message['data']:
        message['data']['action'] = \
            np.array(message['data']['action'])


def denumpyify(message):
    if 'data' in message and 'observation' in message['data']:
        message['data']['observation'] = \
            message['data']['observation'].tolist()


def run_environment(message_queue, response_queue):
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
import gym
import socket
import json
import numpy as np

from . import server


class NetworkEnv(gym.Env):
    _delimiter = server._delimiter
    _encoding = server._encoding
    _read_buffer = b''
    _commands = ['init', 'reset', 'step']

    def __init__(self, address, port, env_name, **env_config):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((address, port))

        print('Connected to server, sending command')

        self.send_command('init', {'env': env_name, 'config': env_config})

        print('Sent init command, waiting for response')

        response = self.receive_command()
        print("Response received: ", response)
        if response['command'] != 'confirm':
            # TODO something went wrong!
            pass

        print("NetworkEnv initiated")

    def send_command(self, command, data = None):
        if command not in self._commands:
            # TODO unsupported command, raise an error
            return

        if data is not None:
            message = {
                'command': command,
                'data': data
            }
        else:
            message = {
                'command': command
            }

        self.socket.sendall(json.dumps(message).encode(self._encoding) \
                            + self._delimiter)

    def receive_command(self):
        while self._delimiter not in self._read_buffer:
            print("Read buffer: ", self._read_buffer.decode(self._encoding))
            data = self.socket.recv(1024)
            print("Data received")
            if not data:
                self.close()
                return
                # TODO connection is broken, close it on this side as well
            self._read_buffer += data

        response, self._read_buffer = \
            self._read_buffer.split(self._delimiter, maxsplit=1)

        return json.loads(response.decode('utf-8'))

    def reset(self):
        self.send_command('reset')
        response = self.receive_command()

        if response['command'] != 'confirm':
            # TODO something went wrong!
            pass

        return np.array(response['data']['observation'])

    def step(self, action):
        self.send_command('step', {'action': action.tolist()})

        response = self.receive_command()

        if response['command'] == 'confirm':
            data = response['data']

            observation = np.array(data['observation'])
            reward = data['reward']
            done = data['done']
            info = data['info']

        else:
            pass
            # TODO something went wrong

        return observation, reward, done, info

    def close(self):
        # TODO dont forget to close the socket and connection
        self.socket.close()

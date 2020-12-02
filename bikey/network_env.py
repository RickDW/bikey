import gym
import socket
import json
import numpy as np


class NetworkEnv(gym.Env):
    _delimitter = '<END>'
    _encoding = 'utf-8'
    _readbuffer = b''

    def __init__(self, address, port, env_name, **env_options):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(address, port)

        self.send_command('init', {'env': env_name, 'options': env_options})

        response = self.receive_command()
        if response['command'] != 'confirm':
            # TODO something went wrong!
            pass

    def send_command(self, command, data = None):
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
                            + self._delimitter)

    def receive_command(self):
        while self._delimitter not in self._readbuffer:
            data = self.socket.recv(1024)
            if not data:
                break # TODO connection is broken, close it on this side as well
            self._readbuffer += data

        response, self._readbuffer = \
            self._readbuffer.split(self._delimitter, max_splits = 1)

        return response.decode('utf-8')

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
            # TODO something went wrong

        return observation, reward, done, info

    def close(self):
        # TODO dont forget to close the socket and connection
        self.socket.close()
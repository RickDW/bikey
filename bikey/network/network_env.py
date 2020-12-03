import gym
import socket
import json
import numpy as np

from . import server


class NetworkEnv(gym.Env):
    """
    Controls another OpenAI gym environment over the internet.

    This environment connects to an environment server that can be located
    anywhere on a network as long as it is reachable. It then exposes the
    standard commands reset(), step(), and close() that allow you to control
    the environment on the server.

    WARNING: The current iteration of the NetworkEnv does NOT have any kind of
    encryption or authentication, be careful with the data that you send across
    the network. If this project continues, this will change in a future
    version.

    The communication is performed on a TCP connection, and data is transmitted
    in JSON form. Messages are delimited using the '<END>' token, meaning this
    token should not be part of any of the data you send. At the moment the
    actions and observations are expected to be numpy arrays, this may change
    in a future version.
    """
    _delimiter = server._delimiter
    _encoding = server._encoding
    _read_buffer = b''

    def __init__(self, address, port, env_name, **env_config):
        """
        Connects to the server and tells it to initialize the environment.

        Arguments:
        address -- The IPv4 address of the server
        port -- The port number to connect to
        env_name -- Name of the environment passed to gym.make()
        env_config -- Optional parameters passed to the gym.make()
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((address, port))

        print('Connected to server, sending command')

        self._send_command('init', {'env': env_name, 'config': env_config})

        print('Sent init command, waiting for response')

        response = self._receive_command()
        print("Response received: ", response)
        if response['command'] != 'confirm':
            # TODO something went wrong!
            pass

        print("NetworkEnv initiated")

    def reset(self):
        """
        Tells the server to reset the environment, returns initial observation.

        Returns:
        Initial observation as defined by the used environment.
        """
        self._send_command('reset')
        response = self._receive_command()

        if response['command'] != 'confirm':
            # TODO something went wrong!
            pass

        return np.array(response['data']['observation'])

    def step(self, action):
        """
        Tells the server to perform one step, returns the usual variables.

        Arguments:
        action -- The action performed by the agent

        Returns:
        A four tuple containing
        - The observation
        - The reward
        - Whether the episode is done
        - Additional info useful for debugging
        """
        self._send_command('step', {'action': action.tolist()})

        response = self._receive_command()

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
        """
        Disconnect from the server.
        """
        self.socket.close()

    def _send_command(self, command, data = None):
        """
        Utility function used to send commands to the server.

        All data is sent in a JSON dictionary:
        {'command': <command>, 'data':<data>} or
        {'command': <command>} when data is None.

        Arguments:
        command -- The contents assigned to 'command'
        data -- The contents assigned to 'data'
        """
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

    def _receive_command(self):
        """
        Utility function used to receive commands from the server.

        Returns:
        A python dictionary containing 'command' and possibly 'data'.
        """
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

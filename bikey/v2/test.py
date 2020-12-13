from bikey.v2.simulink_process import matlab_handler

import gym
import socket
import multiprocessing as mp
import os
import numpy as np
import json


class SpacarEnv(gym.Env):
    _message_terminator = b'\n'
    _encoding = 'utf-8'

    def __init__(self, simulink_file, spacar_file, working_dir = os.getcwd(),
                 template_dir = None, copy_simulink = False, copy_spacar =
                 False, first_action = np.zeros((3,)), output_sbd = False,
                 use_spadraw = False, matlab_params = ''):
        super().__init__()

        config = {
            'simulink_file': simulink_file,
            'spacar_file': spacar_file,
            'working_dir': working_dir,
            'template_dir': template_dir,
            'copy_simulink': copy_simulink,
            'copy_spacar': copy_spacar,
            'output_sbd': output_sbd,
            'use_spadraw': use_spadraw,
            'matlab_params': matlab_params
        }
        self._setup(config)

        self.first_action = first_action

    def _setup(self, config):
        # create the server socket to which the simulation will connect
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('127.0.0.1', 0))  # let OS choose an available port
        self.server.listen()
        port = self.server.getsockname()[1]  # the chosen port
        print(f"Server socket listening on port {port}")

        events = (None,)  # TODO add threading.Events for communication

        # start a process in which matlab will run
        # self.process = mp.Process(target = matlab_handler,
        #                           args = (config, port, events))
        # self.process.start()
        # print("Matlab process launched")

    def reset(self):
        client, address = self.server.accept()
        print("Connected to matlab tcp client")
        # TODO close communications and notify process of new simulation
        self.client = client
        self.read_buffer = b''

        self.x = 0

        observation, *_ = self.step(self.first_action)

        return observation

    def step(self, action):
        # TODO
        print("Waiting for a message")
        message = self._receive_message()
        print("Message received in step:", message)

        self._send_message([0, 0, 0])

        return None, 0, False, {}

    def close(self):
        self.server.close()
        print("Server socket closed")
        print(f"Sent {self.x} messages since last reset")

        # self.process.join()
        print("Process is dead")

    def _receive_message(self):
        while not self._message_terminator in self.read_buffer:
            data = self.client.recv(1024)

            if not data:
                print("Connection to matlab was broken")
                return
                # TODO: handle broken connection

            self.read_buffer += self.client.recv(1024)
            print("In the buffer:", self.read_buffer)

        raw_message, self.read_buffer = self.read_buffer.split(
            self._message_terminator, maxsplit = 1)

        message = json.loads(raw_message.decode(self._encoding))

        # TODO numpyify any arrays?

        return message

    def _send_message(self, message):
        self.client.sendall(json.dumps(message).encode(self._encoding)
                            + self._message_terminator)


if __name__ == '__main__':
    env = SpacarEnv(
        'icttest.slx',
        'bicycle.dat',
        copy_simulink = True,
        copy_spacar = True,
        matlab_params = '-desktop -nosplash')

    env.reset()

    while True:
        msg = env._receive_message()

        print("Message received:")
        print(msg)

        input("Press enter to send response")

        env._send_message([0, 0, 0])
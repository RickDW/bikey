from bikey.v2.simulink_process import matlab_handler

import gym
import socket
import multiprocessing as mp
import os
import numpy as np


# only settings supported by SpacarEnv.change_settings will have an effect
# TODO: make all of these options arguments of the __init__ function
_default_sim_config = {
    "spacar_file": "bicycle.dat",
    "output_sbd": False,
    "use_spadraw": False
}


class SpacarEnv(gym.Env):
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
            'first_action': first_action,
            'output_sbd': output_sbd,
            'use_spadraw': use_spadraw,
            'matlab_params': matlab_params
        }
        self._setup(config)

    def _setup(self, config):
        # create the server socket to which the simulation will connect
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('127.0.0.1', 0))  # let OS choose an available port
        self.server.listen()
        port = self.server.getsockname()[1]  # the chosen port
        print(f"Server socket listening on port {port}")

        events = (None,)  # TODO add threading.Events for communication

        # start a process in which matlab will run
        self.process = mp.Process(target = matlab_handler,
                                  args = (config, port, events))
        self.process.start()
        print("Matlab process launched")

    def reset(self):
        client, address = self.server.accept()
        # TODO close communications and notify process of new simulation
        self.client = client

        self.x = 0

    def step(self, action):
        # TODO
        message = self._receive_message()

        self._send_message("placeholder")

    def close(self):
        self.server.close()
        print("Server socket closed")
        print(f"Sent {self.x} messages since last reset")

        self.process.join()
        print("Process is dead")

    def _receive_message(self):
        pass  # TODO

    def _send_message(self, message):
        pass  # TODO


if __name__ == '__main__':
    env = SpacarEnv(
        'inputtest.slx',
        'bicycle.dat',
        copy_simulink = True,
        copy_spacar = True)

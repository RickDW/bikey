import ssl  # TODO: make this optional on windows? see note below
import matlab.engine

import gym
import bikey.utils
import numpy as np
import os
import socket

# The ssl library only needs to be imported on linux. Apparently the system's
# 'libssl.so' and the one shipped with matlab clash. By loading the system's
# first this issue is prevented. The error that would occur is saved in the
# ssl_error.txt file
# A puzzling aspect of this is that importing matlab.engine in an interpreter
# session works fine, but as soon as it is run in a script it produces the
# error.

# TODO: update all documentation after refactoring

# only settings supported by SpacarEnv.change_settings will have an effect
# TODO: make all of these options arguments of the __init__ function
_default_sim_config = {
    "spacar_file": "bicycle.dat",
    "output_sbd": False,
    "use_spadraw": False
}


class SpacarEnv(gym.Env):
    def __init__(self, simulink_file, working_dir = os.getcwd(), template_dir =
                 None, copy_simulink = False, copy_spacar = False,
                 first_action = np.zeros((3,)), simulink_config =
                 _default_sim_config, matlab_params = ''):
        super().__init__()

        self.matlab = matlab.engine.start_matlab(matlab_params)

        # sets the working directory, allows matlab to find correct files
        self.matlab.cd(working_dir)
        self.working_dir = working_dir

        # set the template directory
        bikey.utils.set_template_dir(template_dir)

        if copy_simulink:
            # copy a simulink model template
            bikey.utils.copy_from_template_dir(simulink_file, working_dir)

        if copy_spacar:
            # copy a spacar model
            bikey.utils.copy_from_template_dir(simulink_config['spacar_file'],
                                               working_dir)

        # open the simulink model
        self.sym_handle = self.matlab.load_system(self.model_name)  # no GUI

        self.simulation_running = False  # TODO make sure this is set to False when needed
        self.model_name = simulink_file[:-4]  # remove the .slx extension

        self.first_action = first_action

        config = _default_sim_config.copy()
        config.update(simulink_config)
        self.simulink_config = config

        self.done = False

        # will be the socket that communicates with the simulink simulation
        self.connection = None

        # TODO, server socket not wrapped in with statement, handle its shutdown
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0)) # port 0 = let OS choose an available port
        s.listen()
        self.port = s.getsockname()[1] # the port the OS chose for the server
        self.server_socket = s

    def reset(self):
        if not self.simulation_running:
            self.matlab.sim(self.sym_handle, nargout = 0) # TODO: should this be non blocking?
            self.simulation_running = True
        else:
            # TODO handle currently running simulation if there is any
            pass

        self.reset_simulink()

        if self.connection is None:
            conn, addr = self.server_socket.accept()
            self.connection = conn

        # TODO: reset the simulation file (set port number, etc.)

        self.done = False

        observation, *_ = self.step(self.first_action)

        return observation

    def reset_simulink(self):
        # TODO: set the server port in the const block
        # TODO: set spacar file + set sbd output option
        pass

    def step(self, actions):
        if not self.simulation_running or self.done:
            return None  # TODO: throw an error instead of returning None

        self._send_message(...)
        self._receive_message(...)

        # subclasses can easily implement their own behaviour here
        reward, done, info = self.process_step(observations)
        eer = "episode_end_reason"

        if self.get_sim_status() == 'stopped':
            info[eer] = "end_of_sim"
            self.done = True

        # allow subclasses to implement their own logic here
        if done:
            if eer in info:
                info[eer] += "/end_of_epi"
            else:
                info[eer] = "end_of_epi"

            self.done = True
            self.send_sim_command('stop')

        return observations, reward, self.done, info

    def _receive_message(self):
        # TODO implement this
        pass

    def _send_message(self, message):
        # TODO implement this
        pass

    def change_settings(self):
        conf = self.simulink_config

        if "spacar_file" in conf:
            # point spacar towards the correct model definition
            # (and remove the .dat file extension)
            spacar_file = conf["spacar_file"][:-4]
            self.matlab.set_param(
                f"{self.model_name}/spacar", 'filename', f"'{spacar_file}'",
                nargout = 0)

        convert = lambda boolean: 'on' if boolean else 'off'

        if "output_sbd" in conf:
            output_sbd = conf["output_sbd"]
            # turn on/off .sbd output (used for making movies of episodes)
            self.matlab.set_param(
                f"{self.model_name}/spacar", "output_sbd",
                convert(output_sbd), nargout = 0)

        if "use_spadraw" in conf:
            use_spadraw = conf["use_spadraw"]
            # turn on/off visualization during episodes
            self.matlab.set_param(
                f"{self.model_name}/spacar", "use_spadraw",
                convert(use_spadraw), nargout = 0)

    def close(self):
        if self.simulation_running:
            self.close_simulink()

        # close matlab
        self.matlab.quit()

    def close_simulink(self):
        # simulink cannot be closed while simulation is running, so stop it
        self.send_sim_command('stop')

        # close simulink and do not save changes
        self.matlab.eval(f"close_system(bdroot, 0)", nargout=0)
        # TODO: figure out what is going on here:
        # can't use the command below since matlab seems to think 0 is a filenme
        # self.session.eval(f"close_system({self.model_name}, 0), nargout=0)
        # gives matlab.engine.MatlabExecutionError: Invalid Simulink object handle
        # self.session.close_system(self.model_name, 0, nargout=0)
        # gives another error

        # remove observations stored in the workspace (variable 'out')
        self.matlab.clear('out', nargout=0)

        # register simulink no longer being available
        self.simulation_running = False

    def process_step(self, observations):
        reward = 0
        done = False
        info = {}
        return reward, done, info

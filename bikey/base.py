import ssl # TODO: make this optional on windows? see note below
import matlab.engine

import gym
import numpy as np
import os
import shutil

# The ssl library only needs to be imported on linux. Apparently the system's
# 'libssl.so' and the one shipped with matlab clash. By loading the system's
# first this issue is prevented. The error that would occur is saved in the
# ssl_error.txt file
# A puzzling aspect of this is that importing matlab.engine in an interpreter
# session works fine, but as soon as it is run in a script it produces the
# error.

# figures out where the current file (i.e. base.py) is located
# this also contains the simulink template file(s)
template_dir = os.path.dirname(os.path.realpath(__file__))
# template_dir = "C:/Users/Rick/Museum/bikey/bikey"
# template_dir = "~/Museum/bikey/bikey"

# TODO: update all documentation after refactoring

# only settings supported by SpacarEnv.change_settings should be used
_default_sim_config = {
    "output_sbd": False,
    "use_spadraw": False
}

class SpacarEnv(gym.Env):
    def __init__(self, action_space, observation_space, simulink_file,
                 simulink_config = _default_sim_config,
                 matlab_params='-desktop', working_dir = os.getcwd()):
        """
        This environment wraps a general physics simulation, run in Spacar.

        # TODO this environment could use a bit more context. Also, a quick
        # overview of how the synchronization works would be nice.

        Keyword arguments:
        simulink_file -- The name of the simulink file that is used to run the
            simulation. This should not include the file's .slx extension. This
            file should be in the current working directory, and cannot be
            located in a nested directory due to the way the simulation
            software works.
        spacar_file -- The name of the spacar file that defines the physical
            properties of the bicycle. This should not include the file's .dat
            extension. This file must be in the current working directory, and
            cannot be located in a nested directory due to the way the
            simulation software works.
        matlab_params -- Parameters passed to Matlab during startup.
        """

        super().__init__()

        # TODO: find out if gym can handle positional arguments
        # TODO: automatically find the correct working directory
        # TODO: check whether specified .slx and .dat files exist
        # TODO: catch all potential errors caused by simulink simulation not
        # yet being available
        # TODO: create a general Simulink simulation class that can run
        # simulations and handle synchronization with Python
        # TODO: having a matlab session for every environment may not be
        # efficient

        self.session = matlab.engine.start_matlab(matlab_params)

        # sets the working directory, allows matlab to find correct files
        self.session.cd(working_dir)
        self.working_dir = working_dir

        self.simulink_loaded = False
        self.simulink_file = simulink_file

        self.settings_changed = False
        self.simulink_config = simulink_config

        # defines which actions and observations are allowed
        self.action_space = action_space
        self.observation_space = observation_space

        # if simulink_loaded is True, done indicates the end of the episode
        self.done = False

    def step(self, actions):
        """
        Performs one step of the simulation and returns the observations.

        Requires Simulink to be loaded. Also requires get_sim_status() ==
        'paused', otherwise this function will not do anything.

        Arguments:
        actions -- A numpy array, with shape conforming to the action space.

        Returns:
        Observations of the system, as defined by get_observations().
        """
        if not self.simulink_loaded or self.done:
            return None # TODO: throw an error instead of returning None

        if self.get_sim_status() == 'paused':
            # TODO: add safeguards that prevent updating action inputs before
            # they are required.
            # TODO: Also check whether 'paused' is the only acceptable
            # option.
            self.update_matlab(actions)
            self.send_sim_command('continue')

            # TODO make sure the simulation is paused/stopped/whatever before
            # reading out the new observations
            observations = self.get_observations()

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

            return (observations, reward, self.done, info)

    def reset(self):
        """
        Makes a new Simulink simulation available and returns the initial
        observations.

        Returns:
        Initial observations of the system, as defined by get_observations().
        """
        # Gracefully shutdown Simulink and clear the observations stored in the
        # workspace
        if self.simulink_loaded:
            self.close_simulink()

        # TODO: make simulink GUI an option of the environment
        self.session.open_system(self.simulink_file, nargout=0) # show simulink GUI
        # self.sym_handle = self.session.load_system(self.simulink_file) # no GUI

        self.simulink_loaded = True

        if not self.settings_changed:
            # make sure the simulation file is set up correctly
            self.change_settings()
            self.settings_changed = True

        self.done = False

        self.send_sim_command('start')
        # (sim will automatically be paused afte one step by the assert block)

        return self.get_observations()

    def copy_template(self, destination_file, template_file = os.path.join(
            template_dir, "template.slx")):
        """
        Makes a copy of template_file.

        If destination_file already exists it will be replaced.
        """

        shutil.copyfile(
            template_file, os.path.join(self.working_dir, destination_file))

    def change_settings(self):
        """
        Makes some changes to the opened Simulink file and saves them.
        """
        conf = self.simulink_config

        if "initial_action" in conf:
            # set the action that is performed once when the env is reset
            str_repr = str(conf["initial_action"].flatten())
            self.session.set_param(
                f"{self.simulink_file}/actions", 'value', str_repr, nargout = 0)

        if "spacar_file" in conf:
            # point spacar towards the correct model definition
            spacar_file = conf["spacar_file"]
            self.session.set_param(
                f"{self.simulink_file}/spacar", 'filename', f"'{spacar_file}'",
                nargout = 0)

        convert = lambda boolean: 'on' if boolean else 'off'

        if "output_sbd" in conf:
            output_sbd = conf["output_sbd"]
            # turn on/off .sbd output (used for making movies of episodes)
            self.session.set_param(
                f"{self.simulink_file}/spacar", "output_sbd",
                convert(output_sbd), nargout = 0)

        if "use_spadraw" in conf:
            use_spadraw = conf["use_spadraw"]
            # turn on/off visualization during episodes
            self.session.set_param(
                f"{self.simulink_file}/spacar", "use_spadraw",
                convert(use_spadraw), nargout = 0)

        # save changes
        self.session.save_system(self.simulink_file)

    def close(self):
        """
        Shutdown Simulink and Matlab.
        """
        if self.simulink_loaded:
            self.close_simulink()

        # close matlab
        self.session.quit()

    def close_simulink(self):
        """
        Stop the Simulink simulation, close Simulink, and clean the workspace.

        Should only be called if env.simulink_loaded is True, i.e. anytime after
        a env.reset(), but not after env.close() or env.close_simulink(). will
        only display a warning message if this is ignored.
        """
        # simulink cannot be closed while simulation is running, so stop it
        self.send_sim_command('stop')

        # close simulink
        self.session.eval(f"close_system(bdroot, 0)", nargout=0)
        # TODO: figure out what is going on here:
        # can't use the command below since matlab seems to think 0 is a filenme
        # self.session.eval(f"close_system({self.simulink_file}, 0), nargout=0)
        # gives matlab.engine.MatlabExecutionError: Invalid Simulink object handle
        # self.session.close_system(self.simulink_file, 0, nargout=0)
        # gives another error

        # remove observations stored in the workspace (variable 'out')
        self.session.clear('out', nargout=0)

        # register simulink no longer being available
        self.simulink_loaded = False

    def update_matlab(self, actions):
        """
        Updates block contents in the Simulink simulation.

        This function tells Simulink which actions are performed in the next
        step, as well as the simulation time from Python's perspective.

        Arguments:
        actions -- A numpy array with shape conforming to the action space.
        """
        string_repr = str(actions.flatten())
        self.session.set_param(
            f'{self.simulink_file}/actions', 'value', string_repr, nargout=0)

        # TODO remove this part of the synchronization mechanism, seems
        # redundant
        simulation_time_matlab = self.session.get_param(
            self.simulink_file, 'SimulationTime')
        self.session.set_param(
            f'{self.simulink_file}/simulation_time_python', 'value',
            str(simulation_time_matlab), nargout=0)

    def send_sim_command(self, command):
        """
        Sends a command to the Simulink simulation, if it is loaded.

        Arguments:
        command -- A string containing the command. For documentation of
            possible values consult the Matlab documentation. Examples are
            'start', 'pause', 'continue', 'stop', and 'update'.
        """
        if self.simulink_loaded:
            self.session.set_param(
                self.simulink_file, 'SimulationCommand', command, nargout=0)

    def get_observations(self):
        """
        Returns the output of the current simulation step.

        Returns None if simulation has not yet been started.

        Returns:
        A numpy array with shape conforming to the defined observation space,
        or None if the simulation has not been started.
        """
        if self.session.exist('out'):
            return np.array(self.session.eval('out.observations')).T
        else:
            return None

    def get_sim_status(self):
        """
        Returns the status of the Simulink simulation, as reported by Matlab.

        Returns:
        A string describing the status of the Simulink simulation. For specific
        values consult Matlab's documentation: the command you are looking for
        is get_param(..., 'SimulationStatus')
        """
        # TODO: throw an error if simulink is not loaded
        # TODO: also throw an error if matlab is no longer active
        return self.session.get_param(self.simulink_file, 'SimulationStatus')

    def process_step(self, observations):
        reward = 0
        done = False
        info = {}
        return (reward, done, info)

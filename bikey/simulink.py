import ssl  # TODO: make this optional on windows? see note below
import matlab.engine
import gym
import numpy as np
import os
import bikey.utils

# The ssl library only needs to be imported on linux. Apparently the system's
# 'libssl.so' and the one shipped with matlab clash. By loading the system's
# first this issue is prevented. The error that occurs is saved in the
# ssl_error.txt file in the repository.
# A puzzling aspect of this is that importing matlab.engine in an interpreter
# session works fine, but as soon as it is run in a script it produces the
# error.

# TODO: update all documentation after refactoring


class SimulinkEnv(gym.Env):
    def __init__(self, 
            simulink_file: str,
            initial_action: np.array,
            working_dir: str = os.getcwd(),
            copy_simulink: bool = False,
            template_dir: str = None,
            matlab_params: str = '-desktop'):
        """
        This environment interfaces with a Simulink simulation.

        The Simulink simulation that will be running is defined in
        simulink_file. It should be located in working_dir, but it is also
        possible to copy a template from a template directory. To use this copy
        mechanism, set copy_simulink to True. By default, the template
        directory in bikey's installation directory is used. This directory
        contains a file with the basic template that is required for bikey's
        interface to work. It is also possible to use your own template
        directory by setting template_dir to its path.

        The first action # TODO: figure out a way for the first action to not be specified in the constructor

        simulink_file should be located in the working_dir. However, if
        copy_simulink is True, then it will be copied from the template
        directory. The copy will overwrite a file by the same name if it
        exists.

        While the simulink_file contains almost everything needed for a
        simulation to be run, there are some settings that will be different
        for every environment. These options can be specified in
        simulink_config. The available options can be found in the
        documentation of SpacarEnv.change_settings(). One of these options is
        the spacar_file. With copy_spacar you can copy a spacar model from the
        template directory, this is done in the same way as copy_simulink.

        Finally, some parameters can be passed to Matlab at startup with
        matlab_params.

        # TODO a quick overview of how the synchronization works would be nice

        Keyword arguments:
        simulink_file -- The name of the simulink file that is used to run the
            simulation. This should include the file's .slx extension.
        working_dir -- The working directory for this environment's Matlab
            session. Any generated output files can be found here.
        template_dir -- If this is set to anything but None the global template
            directory will be set to this.
        copy_simulink -- If True this will copy a simulink model from the
            template directory into the working directory.
        copy_spacar -- If True this will copy a spacar model from the template
            directory into the working directory.
        simulink_config -- The specific configuration applied to the
            simulink_file by SpacarEnv.change_settings().
        matlab_params -- Parameters passed to Matlab at startup.
        """

        super().__init__()

        # TODO: check whether the specified .slx and .dat files exist
        # TODO: having a matlab session for every environment may not be
        # efficient

        if template_dir:
            self.template_dir = template_dir
        else:
            self.template_dir = bikey.utils.standard_template_dir()

        # launch Matlab
        self.session = matlab.engine.start_matlab(matlab_params)
        self.session_active = True

        # set the working directory so Matlab will find the simulation files
        self.session.cd(working_dir)
        self.working_dir = working_dir

        # TODO: is this necessary?
        # disable matlab's notification sound
        self.session.eval('beep off', nargout=0)

        if copy_simulink:
            # create a copy of the specified template in the working dir
            bikey.utils.copy_from_template_dir(
                self.template_dir, simulink_file, working_dir)

        self.simulink_loaded = False
        self.model_name = simulink_file[:-4]  # remove the .slx extension

        # if simulink_loaded is True, done indicates the end of the episode
        self.done = False

        self.initial_action = initial_action


    def reset(self):
        """
        Ready a new Simulink simulation and return the initial observation.

        Returns:
        Initial observation of the system, as defined by get_observations()
        """
        # gracefully shutdown Simulink and clear the observations stored in the
        # workspace
        if self.simulink_loaded:
            self.close_simulink()

        # TODO: make simulink GUI an option of the environment
        # open the simulink model
        self.session.open_system(self.model_name, nargout=0)
        # self.sym_handle = self.session.load_system(self.model_name) # no GUI

        self.simulink_loaded = True
        self.done = False

        # set the initial action before starting the simulation
        self.update_matlab(self.initial_action)

        self.send_sim_command('start')
        # (sim will automatically be paused afte one step by the assert block)

        return self.get_observations()


    def step(self, actions):
        """
        Performs one step of the simulation and returns output of this step.

        Requires Simulink to be loaded. Also requires get_sim_status() ==
        'paused', otherwise this function will not do anything.

        Arguments:
        actions -- A numpy array, with shape conforming to the action space.

        Returns:
        A tuple containing:
        - Observation of the system, as defined by get_observations()
        - Reward for this time step, a float
        - A boolean describing whether the end of the episode has been reached
        - General information for this time step
        """
        
        if not self.simulink_loaded:
            raise RuntimeError("Simulink is not loaded; cannot step through env")

        if self.done:
            raise RuntimeError("The episode has terminated; cannot step through env")

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

            # TODO: allow subclasses to implement their own logic here
            if done:
                if eer in info:
                    info[eer] += "/end_of_epi"
                else:
                    info[eer] = "end_of_epi"

                self.done = True
                self.send_sim_command('stop')

            return observations, reward, self.done, info


    def process_step(self, observations):
        """
        Placeholder function to be overwritten by subclass.

        This function defines the rewards, when to end an episode, and what
        general info is given out at every time step.

        Arguments:
        observations -- Observations of the current time step, as defined by
            get_observations()

        Returns:
        A tuple structured the same way the output of step() is.
        """
        # TODO: make this an abstract method / raise unimplemented error?
        reward = 0
        done = False
        info = {}
        return reward, done, info


    def update_matlab(self, actions):
        """
        Updates block contents in the Simulink simulation.

        This function tells Simulink which actions are performed in the next
        step, as well as the simulation time from Python's perspective. This
        last step is crucial, since it keeps Python and Simulink synchronized.

        Arguments:
        actions -- A numpy array with shape conforming to the action space.
        """
        string_repr = str(actions.flatten())
        self.session.set_param(
            f'{self.model_name}/actions', 'value', string_repr, nargout=0)

        # TODO remove this part of the synchronization mechanism, seems
        # redundant
        simulation_time_matlab = self.session.get_param(
            self.model_name, 'SimulationTime')
        self.session.set_param(
            f'{self.model_name}/simulation_time_python', 'value',
            str(simulation_time_matlab), nargout=0)


    def get_observations(self):
        """
        Returns the output of the current simulation step.

        Returns None if simulation has not yet been started.

        Returns:
        A numpy array with shape conforming to the defined observation space,
        or None if the simulation has not been started.
        """
        if not self.simulink_loaded:
            raise RuntimeError("Cannot obtain observation when Simulink isn't loaded")

        if self.session.exist('out'):
            return np.array(self.session.eval('out.observations')).flatten()

        else:
            raise ValueError("Variable 'out' does not exist in the Matlab workspace")


    def get_sim_status(self):
        """
        Returns the status of the Simulink simulation, as reported by Matlab.

        Returns:
        A string describing the status of the Simulink simulation. For specific
        values consult Matlab's documentation: the command you are looking for
        is get_param(..., 'SimulationStatus')
        """
        if not self.simulink_loaded:
            raise RuntimeError("Cannot obtain simulation status when Simulink isn't loaded.")

        return self.session.get_param(self.model_name, 'SimulationStatus')


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
                self.model_name, 'SimulationCommand', command, nargout=0)

        else:
            raise RuntimeError("Cannot send a command to Simulink when it isn't loaded")


    def close(self):
        """
        Shutdown Simulink and Matlab.
        """
        if self.simulink_loaded:
            self.close_simulink()

        if self.session_active:
            # close matlab
            self.session.quit()

            self.session_active = False


    def close_simulink(self):
        """
        Stop the Simulink simulation, close Simulink, and clean the workspace.

        Should only be called if env.simulink_loaded is True, i.e. anytime after
        an env.reset(), but not after env.close() or env.close_simulink().
        However this will only display a warning message if this is ignored.
        """

        # simulink cannot be closed while simulation is running, so stop it
        self.send_sim_command('stop')

        # close simulink and do not save changes
        self.session.eval(f"close_system(bdroot, 0)", nargout=0)
        # TODO: figure out what is going on here:
        # can't use the command below since matlab seems to think 0 is a filenme
        # self.session.eval(f"close_system({self.model_name}, 0), nargout=0)
        # gives matlab.engine.MatlabExecutionError: Invalid Simulink object handle
        # self.session.close_system(self.model_name, 0, nargout=0)
        # gives another error

        # remove old observations stored in the workspace (variable 'out')
        self.session.clear('out', nargout=0)

        # register simulink as no longer being available
        self.simulink_loaded = False

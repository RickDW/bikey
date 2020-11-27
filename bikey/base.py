from math import inf, pi
import numpy as np
import gym
import ssl # TODO: make this optional on windows? see note below
import matlab.engine

# The ssl library only needs to be imported on linux. Apparently the system's
# 'libssl.so' and the one shipped with matlab clash. By loading the system's
# first this issue is prevented. The error that would occur is saved in the
# ssl_error.txt file
# A puzzling aspect of this is that importing matlab.engine in an interpreter
# session works fine, but as soon as it is run in a script it produces the
# error.

WORKING_DIR = "C:/Users/Rick/Museum/bikey/bikey"
# WORKING_DIR = "~/Museum/bikey/bikey"

# Properties of the motors/servos used in the bicycle robot, torques in
# newton-meters

maxonEC90 = {
    "stallTorque": 4.940,
    "nominalTorque": 0.44,
    "limitedTorque": 0.4
}

maxonF2140 = {
    "stallTorque": 0.031,
    "nominalTorque": 0.012,
    "limitedTorque": 0.01
}

transmission_ratios = {
    "steering": 30,
    "bodyLeaning": 1,
    "propulsion": 1
}

class BaseBicycleEnv(gym.Env):
    metadata = {'render.modes': []}

    def __init__(self, simulink_file='bicycle', spacar_file='bicycle',
                 matlab_params=''):
        """
        This environment wraps a physics simulation of a scaled down bicycle.

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

        # TODO: catch all potential errors caused by simulink simulation not
        # yet being available

        # TODO: create a general Simulink simulation class that can run
        # simulations and handle synchronization with Python
        self.done = False
        self.leaning_limit = 20 * (2 * pi / 360) # radians
        self.simulink_loaded = False
        self.simulink_file = simulink_file

        # TODO: having a matlab session for every environment may not be
        # efficient

        # TODO: make sure the working directory is set correctly before
        # starting matlab / check whether specified .slx and .dat files exist

        self.matlab = matlab.engine.start_matlab(matlab_params)

        # TODO: automatically find the correct working directory
        # sets the working directory, allows matlab to find correct files
        self.matlab.cd(WORKING_DIR)

        torque_limit_propulsion = \
            maxonEC90["limitedTorque"] * transmission_ratios["propulsion"]
        torque_limit_steering = \
            maxonEC90["limitedTorque"] * transmission_ratios["steering"]
        torque_limit_leaning = \
            maxonF2140["limitedTorque"] * transmission_ratios["bodyLeaning"]

        torque_limits = np.array([
            [torque_limit_steering],
            [torque_limit_leaning],
            [torque_limit_propulsion]],
            dtype = np.float32)

        #define actions
        self.action_space = gym.spaces.Box(
                low = -torque_limits,
                high = torque_limits,
                shape = (3, 1),
                dtype = np.float32)

        infinity = np.array([[inf], [inf], [inf], [inf], [inf], [inf]],
                            dtype = np.float32)

        # define observations
        # TODO: give a better description of the observations?
        self.observation_space = gym.spaces.Box(
                low = -infinity,
                high = infinity,
                shape = (6, 1),
                dtype = np.float32)

        # define rewards
        self.reward_range = (-inf, inf) #TODO

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

            observations = self.get_observations()
            info = {}
            reward = 1 # 1 point for every step, as long as you can keep riding

            if self.get_sim_status() == 'stopped':
                info["simulationStopped"] = True
                self.done = True
                self.send_sim_command('stop')

            leaning_angle = abs(observations[2])
            if leaning_angle > self.leaning_limit:
                info["largeLeanAngle"] = True
                self.done = True
                self.send_sim_command('stop')

            # TODO make sure the simulation is paused/stopped/whatever before
            # reading out the new observations
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
        self.matlab.open_system(self.simulink_file, nargout=0) # show simulink GUI
        # self.sym_handle = self.matlab.load_system(self.simulink_file) # no GUI

        self.simulink_loaded = True
        self.done = False

        self.send_sim_command('start')
        # (sim will automatically be paused afte one step by the assert block)

        return self.get_observations()

    def render(self, mode='human'):
        """
        Render the environment. Not supported for this environment.

        Arguments:
        mode -- The type of render action to perform.
        """
        super().render(mode=mode) # raise an exception

    def close(self):
        """
        Shutdown Simulink and Matlab.
        """
        if self.simulink_loaded:
            self.close_simulink()

        # close matlab
        self.matlab.quit()

    def close_simulink(self):
        """
        Stop the Simulink simulation, close Simulink, and clean workspace.

        Should only be called if env.simulink_loaded is True, i.e. anytime after
        a env.reset(), but not after env.close() or env.close_simulink(). will
        only display a warning message if this is ignored.
        """
        # simulink cannot be closed while simulation is running, so stop it
        self.send_sim_command('stop')

        # close simulink
        self.matlab.eval(f"close_system(bdroot, 0)", nargout=0)
        # TODO: figure out what is going on here:
        # can't use the command below since matlab seems to think 0 is a filenme
        # self.matlab.eval(f"close_system({self.simulink_file}, 0), nargout=0)
        # gives matlab.engine.MatlabExecutionError: Invalid Simulink object handle
        # self.matlab.close_system(self.simulink_file, 0, nargout=0)
        # gives another error

        # remove observations stored in the workspace (variable 'out')
        self.matlab.clear('out', nargout=0)

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
        self.matlab.set_param(
            f'{self.simulink_file}/actions', 'value', string_repr, nargout=0)

        simulation_time_matlab = self.matlab.get_param(
            f'{self.simulink_file}', 'SimulationTime')

        self.matlab.set_param(
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
            self.matlab.set_param(
                self.simulink_file, 'SimulationCommand', command, nargout=0)

    def get_observations(self):
        """
        Returns the output of the current simulation step.

        Returns None if simulation has not yet been started.

        Returns:
        A numpy array with shape conforming to the defined observation space,
        or None if the simulation has not been started.
        """
        if self.matlab.exist('out'):
            return np.array(self.matlab.eval('out.observations')).T
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
        return self.matlab.get_param(self.simulink_file, 'SimulationStatus')

import gym
from bikey.spacar import SpacarEnv
from math import inf, pi
import numpy as np
import os

# Properties of the motors/servos used in the bicycle robot, torques in
# Newton-meters

maxonEC90 = {
    "stall_torque": 4.940,
    "nominal_torque": 0.44,
    "limited_torque": 0.4
}

maxonF2140 = {
    "stall_torque": 0.031,
    "nominal_torque": 0.012,
    "limited_torque": 0.01
}

transmission_ratios = {
    "steering": 30,
    "body_leaning": 1,
    "propulsion": 1
}

# only settings supported by SpacarEnv.change_settings will have an effect
_default_sim_config = {
    "initial_action": np.zeros((3, 1)),
    "spacar_file": "bicycle.dat",
    "output_sbd": True,
    "use_spadraw": False
}


class BicycleEnv(SpacarEnv):
    def __init__(self, simulink_file, working_dir = os.getcwd(), template_dir =
                 None, copy_simulink = False, copy_spacar = False,
                 simulink_config = _default_sim_config, matlab_params =
                 '-desktop'):
        """
        This environment wraps the physics simulation of a scaled down bicycle.

        Arguments:
        Arguments are equal to those of bikey.base.SpacarEnv.__init__, consult
            its documentation instead.
        """

        # define actions

        torque_limit_propulsion = \
            maxonEC90["limited_torque"] * transmission_ratios["propulsion"]
        torque_limit_steering = \
            maxonEC90["limited_torque"] * transmission_ratios["steering"]
        torque_limit_leaning = \
            maxonF2140["limited_torque"] * transmission_ratios["body_leaning"]

        torque_limits = np.array([
            [torque_limit_steering],
            [torque_limit_leaning],
            [torque_limit_propulsion]],
            dtype = np.float32)

        action_space = gym.spaces.Box(
                low = -torque_limits,
                high = torque_limits,
                shape = (3, 1),
                dtype = np.float32)

        # define observations

        infinity = np.array([[inf], [inf], [inf], [inf], [inf], [inf]],
                            dtype = np.float32)

        # TODO: give a better description of the observations?
        observation_space = gym.spaces.Box(
                low = -infinity,
                high = infinity,
                shape = (6, 1),
                dtype = np.float32)

        config = _default_sim_config.copy()
        config.update(simulink_config)

        self.action_space = action_space
        self.observation_space = observation_space

        # define rewards
        # TODO: self.reward_range = (-inf, inf)

        super().__init__(simulink_file, working_dir, template_dir,
                         copy_simulink, copy_spacar, config, matlab_params)

        # limits / at what point should the episode terminate?
        deg_to_rad = 2 * pi / 360
        leaning_limit = 30 * deg_to_rad  # leaning angle of bicycle
        steering_limit = 50 * deg_to_rad  # steering angle
        ub_leaning_limit = 30 * deg_to_rad  # leaning angle of upper body

        self.limits = \
            np.array([steering_limit, leaning_limit, ub_leaning_limit])

    def process_step(self, observations):
        """
        Defines the rewards and episode termination rules.

        The episode continues as long as the upper body, handlebars, and the
        bicycle stray to far from configurations that are considered normal
        when a human being cycles in a straight line.

        Arguments:
        observations -- The observations of the current time step, defined by
            get_observations()

        Returns:
        A tuple. The same structure that is expected from SpacarEnv.step()
        """
        reward = 1

        angles = abs(observations.flatten()[1:4])
        done = np.any(angles > self.limits)

        info = {}

        return reward, done, info


gym.envs.register(
    id = "BicycleEnv-v0",
    entry_point = "bikey.bicycle:BicycleEnv"
)

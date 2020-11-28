import base
from math import inf, pi

# Properties of the motors/servos used in the bicycle robot, torques in
# Newton-meters

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

class BicycleEnv(base.SpacarEnv):
    def __init__(self, simulink_file = "simulation", matlab_params='-desktop', 
                 working_dir = os.getcwd()):
        """
        This environment wraps the physics simulation of a scaled down bicycle.

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

        # define actions

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

        super().__init__(action_space, observation_space, simulink_file, 
                         working_dir, matlab_params)

        # define rewards
        self.reward_range = (-inf, inf) #TODO

        # at what point should the episode terminate?
        self.leaning_limit = 20 * (2 * pi / 360) # radians

    def process_step(self, observations):
        reward = 1

        leaning_angle = abs(observations[2])
        done = leaning_angle > self.leaning_limit

        info = {}

        return (reward, done, info)


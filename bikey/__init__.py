import gym.envs
from . import base
from . import bicycle
from . import utils

gym.envs.register(
    id = "BicycleEnv-v0",
    entry_point = "bikey.bicycle:BicycleEnv"
)

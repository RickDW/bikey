import gym.envs
from . import base
from . import bicycle
from . import utils
from . import network


gym.envs.register(
    id = "BicycleEnv-v0",
    entry_point = "bikey.bicycle:BicycleEnv"
)

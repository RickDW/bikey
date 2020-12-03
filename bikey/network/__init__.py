import gym
from . import network_env
from . import server

gym.envs.register(
    id='NetworkEnv-v0',
    entry_point='bikey.network.network_env:NetworkEnv'
)
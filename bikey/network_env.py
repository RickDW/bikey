import gym

class NetworkEnv(gym.Env):
    def __init__(self, env_name, port, **env_options):
        # since it sounds like the DSI cluster has the most flexible connectivity, make this the 'server'
        pass

    def reset(self):
        pass

    def step(self):
        pass

    def close(self):
        pass
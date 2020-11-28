import gym.envs

gym.envs.register(
    id = "BicycleEnv-v0",
    entry_point = "bikey.bicycle:BicycleEnv"
)

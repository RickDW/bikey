from bikey.network.network_env import NetworkEnv

import ray
from ray import tune
from ray.tune.registry import register_env

ray.init()

# make this environment available on every ray process on the cluster
register_env("network_environment", lambda config: NetworkEnv(**config))

analysis = tune.run(
    "PPO",
    stop = {"episode_reward_mean": 15, "num_iterations": 100},
    config = {
        "env": "network_environment",
        "env_config": {
            "address": "127.0.0.1",
            "port": 65432,
            "env_name": "BicycleEnv-v0",
            "simulink_file": "simulation.slx",
            "copy_simulink": True,
            "copy_spacar": True
        },
        "num_gpus": 1,
        "num_workers": 1,
        "lr": tune.grid_search([0.01, 0.001, 0.0001])
    }
)

from bikey.network.network_env import NetworkEnv

import ray
from ray import tune
from ray.tune.registry import register_env
from ray.rllib.agents.callbacks import DefaultCallbacks


class CustomCallback(DefaultCallbacks):
    # def on_episode_start(self, **kwargs):
    #     print(">>> Episode has started!")
    #
    # def on_episode_end(self, **kwargs):
    #     print(">>> Episode has ended")

    def on_sample_end(self, **kwargs):
        print(">>> Sample has ended")

    def on_train_result(self, **kwargs):
        print(">>> Train result available!")


ray.init()

# make this environment available on every ray process on the cluster
register_env("network_environment", lambda config: NetworkEnv(**config))

analysis = tune.run(
    "PPO",
    num_samples = 1,
    stop = {
        "episode_reward_mean": 15,
        "training_iteration": 100
    },
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
        "framework": "tf",
        "gamma": 0.99,
        "lr": 0.0003,
        "num_workers": 1,
        "observation_filter": "MeanStdFilter",
        "num_sgd_iter": 6,
        "vf_share_layers": True,
        "vf_loss_coeff": 0.01,
        "model": {
            "fcnet_hiddens": [32],
            "fcnet_activation": "linear"
        },
        "callbacks": CustomCallback
    }
)

import ray
from ray import tune
from ray.rllib.utils.filter import MeanStdFilter

ray.init()

analysis = tune.run(
    "PPO",
    num_samples = 3,
    stop = {
        "episode_reward_mean": 150
    },
    config = {
        "env": "CartPole-v0",
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
        }
    }
)
import gym, bikey
import numpy as np

env = gym.make(
    'BicycleEnv-v0',
    simulink_file = "copy_test",
    simulink_config = {
        "initial_action": np.array([[1, 2, 3]]).T,
        "spacar_file": "bicycle22",
        "output_sbd": False,
        "use_spadraw": True
    })
env.copy_template('copy_test.slx')
env.reset()

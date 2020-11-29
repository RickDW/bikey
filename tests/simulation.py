import gym
import bikey

import numpy as np
import os

# TODO: use a testing package?

def setup():
    bikey.utils.copy_spacar_file(filename = "bicycle.dat")
    env = gym.make(
        "BicycleEnv-v0",
        simulink_file = "simulation_test.slx",
        create_from_template = True,
        simulink_config = {"output_sbd": True})
        # simulink_config = {
        #     "initial_action": np.array([[0, 0, 0]]).T,
        #     "spacar_file": "bicycle",
        #     "output_sbd": False,
        #     "use_spadraw": False})

    return env

def main():
    env = setup()

    # input("Press <enter> to start test simulation.")

    obs = env.reset()

    action = np.array([[0, 0, 0.01]]).T

    while True:
        results = env.step(action)
        print(results)

        done = results[2]
        if done:
            break

    return env

def action(i):
    return np.array([[i, i+1, i+2]]).T

if __name__ == "__main__":
    env = main()

    input("Press <enter> to end test.")

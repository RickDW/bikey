import gym
import bikey.bicycle

import numpy as np
import os

# TODO: use a testing package?

def main():
    env = gym.make(
        "BicycleEnv-v0",
        simulink_file = "simulation.slx",
        working_dir = os.getcwd(),
        copy_simulink = True,
        copy_spacar = True,
        simulink_config = {
            'spacar_file': 'bicycle.dat'
        })

    input("Press <enter> to start test simulation.")

    obs = env.reset()

    action = np.array([[0, 0, 0.01]]).T
    done = False

    while not done:
        results = env.step(action)
        print(results)
        done = results[2]

    return env

def action(i):
    return np.array([[i, i+1, i+2]]).T

if __name__ == "__main__":
    env = main()

    input("Press <enter> to end test.")

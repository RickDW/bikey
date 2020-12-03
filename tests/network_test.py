import gym
import bikey
from bikey.network.network_env import NetworkEnv
import numpy as np
import os


def setup():
    bikey.utils.copy_spacar_file(filename = "bicycle.dat")

    env = NetworkEnv('127.0.0.1', 65432, 'BicycleEnv-v0',
                     simulink_file='simulation_test.slx',
                     working_dir=os.getcwd(),
                     create_from_template=True)

    return env

def main():
    env = setup()

    # input("Press <enter> to start test simulation.")

    obs = env.reset()

    action = np.array([[0, 0, 0.01]]).T

    done = False

    input("Press enter to start episode")

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

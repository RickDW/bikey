import gym
import bikey

import numpy as np

# TODO: use a testing package?

def setup():
    sim_file = "simulation_test.slx"
    env = gym.make(
        "BicycleEnv-v0",
        simulink_file = sim_file[:-4],
        simulink_config = {
            "initial_action": np.array([[0, 0, 0]]).T,
            "spacar_file": "bicycle",
            "output_sbd": False,
            "use_spadraw": False})

    env.copy_template(sim_file)

    return env

def main():
    env = setup()

    # input("Press <enter> to start test simulation.")

    obs = env.reset()

    action = np.array([[0, 0, 1]]).T

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

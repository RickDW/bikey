from bikey.network.network_env import NetworkEnv
import numpy as np


def main():
    env = NetworkEnv(
        address = '127.0.0.1',
        port = 65432,
        env_name = 'BicycleEnv-v0',
        simulink_file = 'simulation.slx',
        copy_simulink = True,
        copy_spacar = True)

    # input("Press <enter> to start test simulation.")

    obs = env.reset()
    action = np.array([0, 0, 0.001])
    done = False

    input("Press enter to start episode")

    while not done:
        results = env.step(action)
        print(results)
        done = results[2]

    return env


def action(i):
    return np.array([i, i+1, i+2])


if __name__ == "__main__":
    env = main()

    input("Press <enter> to end test.")

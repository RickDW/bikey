from bikey.base import BaseBicycleEnv
import numpy as np

# TODO: use a testing package??

def setup():
    # startup parameters
    matlab_params = '-desktop'
    # name of the simulink file, omitting the .slx extension
    sim_name = 'bicycle'

    env = BaseBicycleEnv(simulink_file=sim_name, matlab_params=matlab_params)

    input("Press <enter> to start test simulation.")

    obs = env.reset()

    action = np.array([[0, 0, 1]]).T

    return env, obs, action

def test(env, action, steps=30):
    for i in range(steps):
        results = env.step(action)
        print(results)
        done = results[2]
        if done:
            break

def action(i):
    return np.array([[i, i+1, i+2]]).T

if __name__ == "__main__":
    env, obs, action = setup()
    test(env, action)

    input("Press <enter> to close Matlab.")

from bikey.simulink import SimulinkEnv
import numpy as np

env = SimulinkEnv(
    simulink_file='simulink_only.slx',
    initial_action=np.array([4, 5, 6]),
    working_dir='tests/',
    copy_simulink=True)

print(env.reset())

for i in range(7):
    obs, rew, done, info = env.step(np.array([0, 1, 2]) + i)

    print(obs, rew, done)

input("Exit?")
# Python package for Simulink-based reinforcement learning environments.

This package contains custom OpenAI Gym environments that can interface with a
Simulink simulation running in Matlab. This can be a powerful combination as
Simulink is often used in engineering fields. Anyone who has experience with
creating Simulink simulations can easily create brand new environments without
learning anything new. At the same time, you can keep using the reinforcement
learning libraries that you are familiar with using in Python.

As a final note, this package was meant to be used with [Spacar](http://spacar.nl/spacar)
simulations, which can be run inside Simulink. Spacar is a software package for
the dynamic modelling and control of flexible multibody systems". The software
is currently being developed by the Faculty of Engineering Technology at the
University of Twente.

**This package is not 100% finished. There is a bug that is likely caused by
Spacar. However, Spacar is supposed to be completely optional, and the code
should run fine without it. I want to refactor the code so it is more suited
for use without Spacar, however I am unsure when this will be
finished. I am aiming for sometime in the next two months.**

## Installation instructions
To install this Python package, use Python's pip tool:

```
# First make sure the git repository (i.e. the directory containing setup.py) is
# set as the working directory, then run this code
pip install .
```

The standard pip options are available, e.g. the -e option allows you to edit
the package after it is installed (both templates and code), without having to
install it again:

```
pip install -e .
# You can now change bikey's code, update files in the template directory, pull
# updates from Github, etc. without having to reinstall bikey
```

## Dependencies
In order to use this package, please make sure Gym and Numpy are installed. The
final package that is needed is the Matlab Engine. Please refer to the
[Matlab documentation](https://nl.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)
for installation instructions.

## Usage
The two main components of this package are the SpacarEnv and BicycleEnv
classes. SpacarEnv is not a full gym environment, therefore only BicycleEnv
is registered as an environment.

To create an environment instance, import the module that defines the bicycle
environment. This will automatically register the environment. This allows you
to create an environment using gym.make:

```
import gym
import bikey.bicycle

env = gym.make("BicycleEnv-v0")
# this creates an instance of the BicycleEnv class

# or

env_with_options = gym.make(
    "BicycleEnv-v0",
    simulink_file="model.slx",
    working_dir="path/to/directory",
    simulink_config={
        ...
    }
    ... # consult the documentation of BicycleEnv for more options
)
```

## Networked environments
The project for which this package is designed has a need for remote execution
of environments, meaning the environment has to be controlled from a different
computer than the one that runs the actual environment. This will add some
latency and may make your training sessions less efficient.

**Warning:** currently the code for the NetworkEnv class lacks basic security
features. The environments that run on the server are completely controlled
by the client, and will run code without question. **Use at your own risk.** If
you trust the client and server nodes, the network, and the environment, then
you will probably be fine, but take this with a mountain of salt.

The NetworkEnv class is designed to be used with any gym environment, but at
the moment it assumes the actions and observations of any underlying
environment are numpy arrays. Another thing to be wary of is the lack of
support for observation spaces and action spaces of any type other than
gym.spaces.Discrete or gym.spaces.Box. If support for other spaces is needed
you could easily implement this yourself, by adding functionality to 
gym_space_to_dict in bikey.network.env_process as well as dict_to_gym_space in
bikey.network.network_env. Simply put the details necessary to describe and
reconstruct a space in a dictionary, and make sure this dictionary can be
serialized as JSON.

Run the `bikey.network.server` script to start an environment server:

```
python -m bikey.network.server

# or use the -h or --help flag to display the command's options:
python -m bikey.network.server -h
```

To shut down the server use the -s or --stop flags:

```
python -m bikey.network.server --stop
```

It should be run **on the machine that started the server**, otherwise the
server will not shut down. This command will not automatically detect the
address and port of a running server: they should be provided to the script.

## Custom Simulink environments (work in progress)
This package makes creating your own Simulink environments as easy as possible.
All you need to do is subclass bikey.spacar.SpacarEnv, override the
process_step() function with the code for your own environment, and set up 
the correct observation and action spaces. The process_step() function defines
the rules of the environment: it determines rewards, when to end an episode,
and additionally it can provide some general info that can be useful when 
debugging a RL training session.

The basic Simulink template file has a very simple Simulink model: actions are
provided to Simulink through a constant block, and outputs are read out from
the Matlab workspace. If you need to customize this feel free to do so, but
make sure there is a constant block with name 'actions', and a block that
saves the last, and only the last, Spacar observation to 'out.observations' in
the Matlab workspace.

Along with all of the settings available when instantiating an environment,
this should give you plenty of room to create any setup you want.

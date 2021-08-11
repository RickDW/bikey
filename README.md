# Python package for Simulink-based reinforcement learning environments.

**This package is not 100% finished. There is a bug that is likely caused by
Spacar. However, Spacar is supposed to be completely optional, and the code
should run fine without it. I want to refactor the code so it is more suited
for Simulink files without Spacar dependencies. I am unsure when this will be
finished, but I am aiming for sometime in the next two months.**

If you are using or improving this package I would love to hear about it.

This package contains custom OpenAI Gym environments that can interface with a
[Spacar](http://spacar.nl/spacar) simulation. Spacar is a software package for
"the dynamic modelling and control of flexible multibody systems". The
software is currently being developed by the Faculty of Engineering Technology
at the University of Twente. With these environments, controllers can be
created using reinforcement learning (RL).

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

Warning: currently the code for the NetworkEnv class lacks basic security
features. I hope to implement some of those in the near future. Pull requests
are welcome.

The NetworkEnv class is designed to be used with any gym environment, but at
the moment it assumes the actions and observations of any underlying
environment are numpy arrays. Another thing to be wary of is the lack of
support for observation spaces and action spaces of any type other than
gym.spaces.Discrete or gym.spaces.Box. If support for other spaces is needed
you could easily implement this yourself, by adding functionality to 
gym_space_to_dict in bikey.network.env_process as well as dict_to_gym_space in
bikey.network.network_env. Simply put the details necessary to describe and
reconstruct a space in a dictionary, and make sure this dictionary can be
converted to JSON.

Run the `bikey.network.server` module to start an environment server:

```
python -m bikey.network.server

# or use the -h flag to display the command's options:
python -m bikey.network.server -h
```

To shut down the server the following command should be executed **on the
machine that started the server**, otherwise it will be ignored:

```
python -m bikey.network.server_shutdown
```

This command will not automatically detect the address and port of a running
server: they should be provided to the script. For an overview of the shutdown
script, run it with the `-h` flag.

## Creating a custom Simulink environment
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

# Python package for simulated control of a robot bicycle

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
the package after it is installed, without having to install it again:

```
pip install -e .
# You can now change the bikey package, pull updates from Github, etc. without
# reinstallation
```

## Usage
The two main components of this package are the SpacarEnv and BicycleEnv
classes. SpacarEnv is not a full gym environment, therefore only BicycleEnv
is registered as an environment.

To create an environment instance, first import the bikey package. This will
automatically register the bicycle environment, which allows gym.make to
create an environment with the specified options.

```
import gym
import bikey

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

## More custom Spacar environments
This package makes creating your own Spacar environments as easy as possible.
All you need to do is to subclass bikey.base.SpacarEnv and override the
process_step() function with your own logic. This function defines the
the rules of the environment: how to determine rewards, when to end an episode,
and additionally some general info that can be useful when debugging your code.

The basic template has a very simple Simulink model: actions are provided to
Spacar, and outputs are read out to the environment. If you need to customize
this feel free to do so, but make sure there is a constant block with name
'actions', and a block that saves the last, and only the last, observation
to 'out.observations' in the Matlab workspace.

Along with all of the settings available when instantiating an environment
this should give you plenty of room to create any setup you want.
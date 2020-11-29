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
classes. The first class can technically be used as a RL environment, but it's
behaviour is not very useful without subclassing it. Therefore it is not
registered as an environment.

To create an environment, first import the bikey package. This will
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
    "simulink_file"="model.slx",
    "working_dir"="path/to/directory",
    "simulink_config"={
        ...
    }
    ... # consult the documentation of BicycleEnv for more options
)
```
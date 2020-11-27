# Python package for simulated control of a robot bicycle

This package contains a custom OpenAI Gym environment that connects to a 
Simulink simulation in Matlab. With this environment a controller can be 
created using reinforcement learning.

## Installation instructions
To install this Python package, use Python's pip tool:

```
# First make sure your working directory is the parent directory of the git 
# repository (i.e. the directory containing setup.py)
python -m pip install bikey
```

The standard pip options are available, e.g. the -e option allows you to edit 
the package after it is installed, without having to install it again:

```
python -m pip install -e bikey
# You can now change the bikey package, pull updates from Github, etc. without
# reinstallation
```

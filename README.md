# Python package for simulated control of a robot bicycle

This package contains a custom OpenAI Gym environment that connects to a
Simulink simulation in Matlab. A controller can be created with this
environment using reinforcement learning.

## Input files **[important]**
For now, the locations of the input files for Simulink and Spacar must be
changed manually in the code. To do this, change the WORKING_DIR variable
inside the base.py module. It is recommended to use an absolute path to avoid
confusion. The specified directory will be the working directory for Matlab.

## Installation instructions
To install this Python package, use Python's pip tool:

```
# First make sure your working directory is the parent directory of the git
# repository (i.e. the directory containing setup.py), then run this code
pip install ./bikey
```

The standard pip options are available, e.g. the -e option allows you to edit
the package after it is installed, without having to install it again:

```
pip install -e ./bikey
# You can now change the bikey package, pull updates from Github, etc. without
# reinstallation
```

import os
import shutil

# figures out where the current file (i.e. utils.py) is located
# this also is the folder where the package is located
template_dir = os.path.dirname(os.path.realpath(__file__))

def copy_spacar_file(dir, filename = "bicycle.dat"):
    src = os.path.join(template_dir, filename)
    dest = os.path.join(dir, filename)

    shutil.copyfile(src, dest)
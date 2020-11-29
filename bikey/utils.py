import os
import shutil

# figures out where the current file (i.e. utils.py) is located
# this also is the folder where the package is located
# template_dir = os.path.dirname(os.path.realpath(__file__))

def copy_spacar_file(filename = "bicycle.dat", dir = os.getcwd()):
    """
    Copies a Spacar model from the bikey template directory.

    Args:
    filename -- The name of the file to be copied.
    dir -- The directory where the file should be copied to.
    """
    src = os.path.join(find_template_dir(), filename)
    dest = os.path.join(dir, filename)

    shutil.copyfile(src, dest)

def find_template_dir():
    """
    Finds the bikey template directory.

    Returns:
    A string describing the path of the template directory.
    """
    # find the directory where util.py is located
    package_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(package_dir, "templates")
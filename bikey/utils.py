import os
import shutil

_custom_template_dir = False
_template_dir = ""

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


def copy_from_template_dir(filename, working_dir=os.getcwd()):
    """
    Copies a file from the template directory to the given working directory.

    Args:
    filename -- The name of the file to be copied.
    working_dir -- The directory where the file should be copied to.
    """
    src = os.path.join(find_template_dir(), filename)
    dest = os.path.join(working_dir, filename)

    shutil.copyfile(src, dest)


def set_template_dir(dir=None):
    """
    Overrides the default template directory that comes with bikey.

    Arguments:
    dir -- the custom template directory. If None the default template
        directory will be used.
    """
    if dir is None:
        # fall back to bikey's default template dir
        _custom_template_dir = False
    else:
        _custom_template_dir = True
        _template_dir = dir


def find_template_dir():
    """
    Finds the bikey template directory.

    Returns:
    A string describing the path of the template directory.
    """
    if _custom_template_dir:
        # return the file path specified by user
        return _template_dir
    else:
        # find the directory where util.py is located
        package_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(package_dir, "templates")
import os
import shutil

_custom_template_dir = False
_template_dir = ""


def copy_from_template_dir(filename, working_dir=os.getcwd()):
    """
    Copy a file from the template directory to the given working directory.

    Args:
    filename -- The filename of the template to be copied.
    working_dir -- The directory where the file should be copied to.
    """
    src = os.path.join(find_template_dir(), filename)
    dest = os.path.join(working_dir, filename)

    shutil.copyfile(src, dest)


def set_template_dir(directory=None):
    """
    Override the default template directory that comes with bikey.

    Arguments:
    dir -- the custom template directory. If None the default template
        directory will be used.
    """
    if directory is None:
        # fall back to bikey's default template dir
        _custom_template_dir = False
    else:
        _custom_template_dir = True
        _template_dir = directory


def find_template_dir():
    """
    Find the template directory where bikey stores Spacar and Simulink templates.

    Returns:
    The path of the template directory.
    """
    if _custom_template_dir:
        # return the file path specified by user
        return _template_dir
    else:
        # find the directory where utils.py is located
        package_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(package_dir, "spacar_templates")

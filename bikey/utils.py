import os
import shutil


def standard_template_dir() -> str:
    """
    Return the template directory containing Simulink and Spacar templates.

    Returns:
    Path to the template directory.
    """
    # find the directory where utils.py is located
    package_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(package_dir, "templates")


def copy_from_template_dir(template_dir: str, template: str, 
        working_dir: str) -> None:
    """
    Create a copy of a template in the working directory.

    Args:
    template_dir -- The directory where templates are stored
    template -- Name of the template file (not a path)
    working_dir -- The working directory, copy will be put here
    """
    src = os.path.join(template_dir, template)
    dest = os.path.join(working_dir, template)

    shutil.copyfile(src, dest)

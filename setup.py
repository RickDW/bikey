import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name = "bikey-spacar-simulation",
    version = "0.2",
    author = "Rick de Wolf",
    description = "Provides OpenAI Gym environments for interfacing with Spacar simulations",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = setuptools.find_packages(),
    classifiers = [

    ],
    python_requires = ">=3.5"
)

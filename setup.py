import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name = "bikey-testing",
    version = "0.1",
    author = "Rick de Wolf",
    description = "Provides an OpenAI Gym environment for a bicycle robot",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = setuptools.find_packages(),
    classifiers = [

    ],
    python_requires = ">=3.5"
)

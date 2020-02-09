from setuptools import find_packages, setup

setup(
    name="gitopscli",
    version="2.1.0",
    packages=find_packages(),
    entry_points={"console_scripts": ["gitopscli = gitopscli.__main__:main"]},
)

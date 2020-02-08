from setuptools import setup

setup(
    name="gitopscli",
    version="0.1.0",
    packages=["gitopscli", "gitopscli.commands", "gitopscli.git", "gitopscli.yaml"],
    entry_points={"console_scripts": ["gitopscli = gitopscli.__main__:main"]},
)

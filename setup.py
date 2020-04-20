from setuptools import find_packages, setup

setup(
    name="gitopscli",
    version="dev",
    packages=find_packages(),
    entry_points={"console_scripts": ["gitopscli = gitopscli.__main__:main"]},
    setup_requires=["wheel"],
    install_requires=["GitPython==3.0.6", "ruamel.yaml==0.16.5", "atlassian-python-api==1.14.5", "PyGithub==1.45",],
)

from setuptools import find_packages, setup

setup(
    name="gitopscli",
    version="0.0.0",
    packages=find_packages(),
    entry_points={"console_scripts": ["gitopscli = gitopscli.__main__:main"]},
    setup_requires=["wheel"],
    install_requires=[
        "GitPython==3.1.32",
        "ruamel.yaml==0.16.5",
        "jsonpath-ng==1.5.3",
        "atlassian-python-api==1.14.5",
        "PyGithub==1.53",
        "python-gitlab==2.6.0",
    ],
)

# Setup

Currently there are two different ways to setup and use the GitOps CLI.

## Docker

The official GitOps CLI Docker image comes with all dependencies pre-installed and ready-to-use. Pull it with:
```bash
docker pull baloise/gitopscli
```
Start the CLI and the print the help page with:
```bash
docker run --rm -it baloise/gitopscli --help
```

## From Source With Virtualenv

Use this for developement and if you want to prevent dependency clashes with other programs in a user installation.

Clone the repository and install the GitOps CLI on your machine:
```bash
git clone https://github.com/baloise/gitopscli.git
cd gitopscli/
poetry install
```
You can now use it from the command line:
```bash
poetry run gitopscli --help
```
If you don't need the CLI anymore, you can uninstall it with
```bash
poetry env remove --all
```

Note: if your poetry is not up to date to handle the files you can use a locally updated version.
Execute the following command in your cloned gitopscli directory to use an updated poetry without changing your system installation:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install poetry # installs it in the venv
```

## From Source Into User Installation

Clone the repository and install the GitOps CLI on your machine:
```bash
git clone https://github.com/baloise/gitopscli.git
pip3 install gitopscli/
```
You can now use it from the command line:
```bash
gitopscli --help
```
If you don't need the CLI anymore, you can uninstall it with
```bash
pip3 uninstall gitopscli
```
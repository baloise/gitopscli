[![Build Status](https://github.com/baloise/gitopscli/actions/workflows/release.yml/badge.svg)](https://github.com/baloise/gitopscli/actions/workflows/release.yml)
[![Latest Release)](https://img.shields.io/github/v/release/baloise/gitopscli)](https://github.com/baloise/gitopscli/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/baloise/gitopscli)](https://hub.docker.com/r/baloise/gitopscli/tags)
[![Python: 3.10](https://img.shields.io/badge/python-3.10-yellow.svg)](https://www.python.org/downloads/release/python-3108/)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![Gitpod](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/baloise/gitopscli) 
[![License](https://img.shields.io/github/license/baloise/gitopscli?color=lightgrey)](https://github.com/baloise/gitopscli/blob/master/LICENSE)

# GitOps CLI

GitOps CLI is a command line interface (CLI) to perform operations on GitOps managed infrastructure repositories, including updates in YAML files.

![GitOps CLI Teaser](docs/assets/images/teaser.png)

## Quick Start
The official GitOps CLI Docker image comes with all dependencies pre-installed and ready-to-use. Pull it with:
```bash
docker pull baloise/gitopscli
```
Start the CLI and the print the help page with:
```bash
docker run --rm -it baloise/gitopscli --help
```

## Features
- Update YAML values in config repository to e.g. deploy an application.
- Add pull request comments.
- Create and delete preview environments in the config repository for a pull request in an app repository.
- Update root config repository with all apps from child config repositories.

For detailed installation and usage instructions, visit [https://baloise.github.io/gitopscli/](https://baloise.github.io/gitopscli/).

## Git Provider Support
Currently, we support BitBucket Server, GitHub and Gitlab.

## Development

### Setup

```bash
python3 -m venv venv  # create and activate virtual environment
source venv/bin/activate  # enter virtual environment
make init  # install dependencies, setup dev gitopscli, install pre-commit hooks, ...
deactivate  # leave virtual environment (after development)
```

### Commands
```bash
make format  # format code
make format-check  # check formatting
make lint  # run linter
make mypy  # run type checks
make test  # run unit tests
make coverage  # run unit tests and create coverage report
make checks  # run all checks (format-check + lint + mypy + test)
make image  # build docker image
make docs  # serves web docs
```

## License
[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)

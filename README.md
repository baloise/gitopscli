
[![Build Status](https://travis-ci.org/baloise-incubator/gitopscli.svg?branch=master)](https://travis-ci.org/baloise-incubator/gitopscli) 
[![Latest Release](https://img.shields.io/github/v/tag/baloise-incubator/gitopscli)](https://hub.docker.com/repository/docker/baloiseincubator/gitopscli/tags?page=1)
[![Python: 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) 
[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/baloise-incubator/gitopscli) 
[![License: GNU GPLv3](https://img.shields.io/badge/license-GNU%20GPLv3-lightgrey.svg)](https://choosealicense.com/licenses/gpl-3.0/) 

# GitOps CLI ![Stability: Experimental](https://img.shields.io/badge/stability-experimental-orange)

GitOps CLI is a command line interface (CLI) to perform operations on GitOps managed infrastructure repositories, including updates in YAML files.

![GitOps CLI Teaser](docs/assets/images/teaser.png)

## Quick Start
The official GitOps CLI Docker image comes with all dependencies pre-installed and ready-to-use. Pull it with:
```bash
docker pull baloiseincubator/gitopscli
```
Start the CLI and the print help page with:
```bash
docker run --rm -it baloiseincubator/gitopscli --help
```

## Features
- Update YAML values in config repository to e.g. deploy an application.
- Add a pull request comments.
- Create and delete preview environments in the config repository for a pull request in an app repository.
- Update root config repository with all apps from child config repository.

For detailed installation and usage instructions, visit [https://baloise-incubator.github.io/gitopscli/](https://baloise-incubator.github.io/gitopscli/).

## Git Provider Support
Currently, we support both BitBucket Server and GitHub.

## License
[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)

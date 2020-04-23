
[![Build Status](https://travis-ci.org/baloise/gitopscli.svg?branch=master)](https://travis-ci.org/baloise/gitopscli) 
[![Latest Release](https://img.shields.io/github/v/tag/baloise/gitopscli)](https://hub.docker.com/r/baloise/gitopscli/tags)
[![Python: 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) 
[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/baloise/gitopscli) 
[![License: Apache License Version 2.0](https://img.shields.io/badge/license-Apache%20License%20Version%202.0-lightgrey.svg)](https://choosealicense.com/licenses/apache-2.0/) 

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
Currently, we support both BitBucket Server and GitHub.

## License
[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)

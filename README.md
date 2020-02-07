# GitOps CLI
[![Build Status](https://travis-ci.org/baloise-incubator/gitopscli.svg?branch=master)](https://travis-ci.org/baloise-incubator/gitopscli) 
[![Latest Release](https://img.shields.io/github/v/tag/baloise-incubator/gitopscli)](https://hub.docker.com/repository/docker/baloiseincubator/gitopscli/tags?page=1)
[![Python: 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) 
[![License: Apache License Version 2.0](https://img.shields.io/badge/license-Apache%20License%20Version%202.0-lightgrey.svg)](https://choosealicense.com/licenses/apache-2.0/) 

GitOps CLI is a command line utility to perform operations on GitOps managed infrastructure repositories, including updates in YAML files.

## Functionality
- [add-pr-comment](doc/commands/add-pr-comment.md): Add a pull request comment
- [create-preview](doc/commands/create-preview.md): Create a preview environment in the config repository for a pull request in an app repository.
- [deploy](doc/commands/deploy.md): Update YAML values in config repository to e.g. deploy an application.
- [sync-apps](doc/commands/sync-apps.md): Update root config repository with all apps from child config repository.

## Git Provider support
Currently, we support both BitBucket Server and GitHub.

## Usage
You can install the Python based GitOps CLI locally on you system or simply run it in a docker container.

### Local (recommended for development)

Clone this repository. Then install the CLI and all its python dependencies via:
```bash
make install
```

You can now use the `gitopscli` command, e.g
```bash
gitopscli --help
```

### Docker
You can find all GitOps CLI docker images on [dockerhub](https://hub.docker.com/r/baloiseincubator/gitopscli/tags). To use the latest version run
```bash
docker run --rm -it baloiseincubator/gitopscli --help
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)

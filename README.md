# GitOps CLI
[![Build Status](https://travis-ci.org/baloise-incubator/gitopscli.svg?branch=master)](https://travis-ci.org/baloise-incubator/gitopscli) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 

GitOps CLI is a command line utility to perform operations on git ops managed infrastructure repositories, including updates in yaml files.

## Installation (dev)

```bash
make install
```

## Usage
```bash
gitopscli deploy --git-provider-url https://bitbucket.baloise.dev \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--organisation "DPL" \
--repository-name "incubator-non-prod" \
--file example/values.yaml \
--branch deploy-$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 5 | head -n 1) \
--values "{image.tag: v0.3.0}" \
--create-pr \
--auto-merge
```

## Usage with Docker
```bash
docker run --rm -it gitopscli deploy [...]
```



## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)

# GitOps CLI
[![Build Status](https://travis-ci.org/baloise-incubator/gitopscli.svg?branch=master)](https://travis-ci.org/baloise-incubator/gitopscli) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 

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

### Usage with Docker
```bash
docker run --rm -it gitopscli deploy [...]
```

## Dev
Install via

```bash
make install
```

Then use it normally like

```bash
gitopscli deploy --help
```

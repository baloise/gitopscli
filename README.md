# GitOps CLI
[![Build Status](https://travis-ci.org/baloise-incubator/gitopscli.svg?branch=master)](https://travis-ci.org/baloise-incubator/gitopscli) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 

GitOps CLI is a command line utility to perform operations on git ops managed infrastructure repositories, including updates in yaml files.

## Git Provider support
Currently, we support both BitBucket Server and GitHub.

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

### Usage with Docker
```bash
docker run --rm -it gitopscli deploy [...]
```

## Supported Operations

Parameter        | Description   | Default
------------ | ------------- | -------------
-f, --file (required) | YAML file path | 
-v, --values (required)| YAML/JSON object with the YAML path as key and the desired value as value |
-b, --branch | Branch to push the changes to | `master`
-u, --username (required)| Git username if Basic Auth should be used |
-p, --password (required)| Git password if Basic Auth should be used |
-j, --git-user| Git Username | `GitOpsCLI`
-e, --git-email| Git User Email | `gitopscli@baloise.dev`
-c, --create-pr| Creates a Pull Request (only when --branch is not master/default branch) | `false`
-a, --auto-merge| Automatically merge the created PR (only valid with --create-pr) | `false`
-o, --organisation (required)| Git organisation/projectKey |
-n, --repository-name (required)| Git repository name (not the URL, e.g. my-repo) |
-s, --git-provider | Git server provider | `bitbucket-server`
-w, --git-provider-url (required if BitBucket) | Git provider base API URL (e.g. https://bitbucket.example.tld) |


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)

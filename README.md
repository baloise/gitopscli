# GitOps CLI
[![Build Status](https://travis-ci.org/baloise-incubator/gitopscli.svg?branch=master)](https://travis-ci.org/baloise-incubator/gitopscli) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 
[![Latest Release](https://img.shields.io/github/v/tag/baloise-incubator/gitopscli)](https://hub.docker.com/repository/docker/baloiseincubator/gitopscli/tags?page=1)

GitOps CLI is a command line utility to perform operations on git ops managed infrastructure repositories, including updates in yaml files.

## Git Provider support
Currently, we support both BitBucket Server and GitHub.

### Docker
```bash
$ docker run --rm -it baloiseincubator/gitopscli deploy [options]
```

## Usage
```
$ gitopscli -h
usage: gitopscli [-h] {deploy,sync-apps,add-pr-comment} ...

GitOps CLI

optional arguments:
  -h, --help            show this help message and exit

commands:
  {deploy,sync-apps,add-pr-comment}
    deploy              Trigger a new deployment by changing YAML values
    sync-apps           Synchronize applications (= every directory) from apps
                        config repository to apps root config
    add-pr-comment      Create a comment on the pull request
```

### `gitopscli deploy`
```bash
$ gitopscli deploy --git-provider-url https://bitbucket.baloise.dev \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "DPL" \
--repository-name "incubator-non-prod" \
--file example/values.yaml \
--branch deploy-$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 5 | head -n 1) \
--values "{image.tag: v0.3.0}" \
--create-pr \
--auto-merge
```

```
$ gitopscli deploy -h
usage: gitopscli deploy [-h] -f FILE -v VALUES [-b BRANCH] [-u USERNAME]
                        [-p PASSWORD] [-j GIT_USER] [-e GIT_EMAIL]
                        [-c [CREATE_PR]] [-a [AUTO_MERGE]] -o ORGANISATION -n
                        REPOSITORY_NAME [-s GIT_PROVIDER]
                        [-w GIT_PROVIDER_URL]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  YAML file path
  -v VALUES, --values VALUES
                        YAML/JSON object with the YAML path as key and the
                        desired value as value
  -b BRANCH, --branch BRANCH
                        Branch to push the changes to
  -u USERNAME, --username USERNAME
                        Git username if Basic Auth should be used
  -p PASSWORD, --password PASSWORD
                        Git password if Basic Auth should be used
  -j GIT_USER, --git-user GIT_USER
                        Git Username
  -e GIT_EMAIL, --git-email GIT_EMAIL
                        Git User Email
  -c [CREATE_PR], --create-pr [CREATE_PR]
                        Creates a Pull Request (only when --branch is not
                        master/default branch)
  -a [AUTO_MERGE], --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  -o ORGANISATION, --organisation ORGANISATION
                        Apps Git organisation/projectKey
  -n REPOSITORY_NAME, --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  -s GIT_PROVIDER, --git-provider GIT_PROVIDER
                        Git server provider
  -w GIT_PROVIDER_URL, --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
```

### `gitopscli sync-apps`

```bash
$ gitopscli sync-apps --git-provider-url https://bitbucket.baloise.dev \
--username "${USERNAME}" \
--password "${PASSWORD}" \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "${organisation}" \
--repository-name "${repository}" \
--root-organisation "DPL" \
--root-repository-name "apps-root-config" 
```

```
$ gitopscli sync-apps -h
usage: gitopscli sync-apps [-h] [-b BRANCH] [-u USERNAME] [-p PASSWORD]
                           [-j GIT_USER] [-e GIT_EMAIL] [-c [CREATE_PR]]
                           [-a [AUTO_MERGE]] -o ORGANISATION -n
                           REPOSITORY_NAME [-s GIT_PROVIDER]
                           [-w GIT_PROVIDER_URL] -i ROOT_ORGANISATION -r
                           ROOT_REPOSITORY_NAME

optional arguments:
  -h, --help            show this help message and exit
  -b BRANCH, --branch BRANCH
                        Branch to push the changes to
  -u USERNAME, --username USERNAME
                        Git username if Basic Auth should be used
  -p PASSWORD, --password PASSWORD
                        Git password if Basic Auth should be used
  -j GIT_USER, --git-user GIT_USER
                        Git Username
  -e GIT_EMAIL, --git-email GIT_EMAIL
                        Git User Email
  -c [CREATE_PR], --create-pr [CREATE_PR]
                        Creates a Pull Request (only when --branch is not
                        master/default branch)
  -a [AUTO_MERGE], --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  -o ORGANISATION, --organisation ORGANISATION
                        Apps Git organisation/projectKey
  -n REPOSITORY_NAME, --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  -s GIT_PROVIDER, --git-provider GIT_PROVIDER
                        Git server provider
  -w GIT_PROVIDER_URL, --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  -i ROOT_ORGANISATION, --root-organisation ROOT_ORGANISATION
                        Apps config repository organisation
  -r ROOT_REPOSITORY_NAME, --root-repository-name ROOT_REPOSITORY_NAME
                        Root config repository organisation
```

### `gitopscli add-pr-comment`

```bash
$ gitopscli add-pr-comment --git-provider-url https://bitbucket.baloise.dev \
--username "${USERNAME}" \
--password "${PASSWORD}" \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "${organisation}" \
--repository-name "${repository}" \
--pr-id 27 \
--text "this is a comment" 
```

```
$ gitopscli add-pr-comment -h
usage: gitopscli add-pr-comment [-h] [-b BRANCH] [-u USERNAME] [-p PASSWORD]
                                [-j GIT_USER] [-e GIT_EMAIL] [-c [CREATE_PR]]
                                [-a [AUTO_MERGE]] -o ORGANISATION -n
                                REPOSITORY_NAME [-s GIT_PROVIDER]
                                [-w GIT_PROVIDER_URL] -i PR_ID -t TEXT

optional arguments:
  -h, --help            show this help message and exit
  -b BRANCH, --branch BRANCH
                        Branch to push the changes to
  -u USERNAME, --username USERNAME
                        Git username if Basic Auth should be used
  -p PASSWORD, --password PASSWORD
                        Git password if Basic Auth should be used
  -j GIT_USER, --git-user GIT_USER
                        Git Username
  -e GIT_EMAIL, --git-email GIT_EMAIL
                        Git User Email
  -c [CREATE_PR], --create-pr [CREATE_PR]
                        Creates a Pull Request (only when --branch is not
                        master/default branch)
  -a [AUTO_MERGE], --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  -o ORGANISATION, --organisation ORGANISATION
                        Apps Git organisation/projectKey
  -n REPOSITORY_NAME, --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  -s GIT_PROVIDER, --git-provider GIT_PROVIDER
                        Git server provider
  -w GIT_PROVIDER_URL, --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  -i PR_ID, --pr-id PR_ID
                        the id of the pull request
  -t TEXT, --text TEXT  the text of the comment
```

### `gitopscli create-preview`

```bash
$ gitopscli create-preview --git-provider-url https://bitbucket.baloise.dev \
--username "${USERNAME}" \
--password "${PASSWORD}" \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "${organisation}" \
--repository-name "${repository}" \
--branch "somebranchname" \
--create-pr \
--auto-merge
```

```
$ gitopscli create-preview -h
usage: gitopscli create-preview [-h] [-b BRANCH] [-u USERNAME] [-p PASSWORD]
                                [-j GIT_USER] [-e GIT_EMAIL] [-c [CREATE_PR]]
                                [-a [AUTO_MERGE]] -o ORGANISATION -n
                                REPOSITORY_NAME [-s GIT_PROVIDER]
                                [-w GIT_PROVIDER_URL]

optional arguments:
  -h, --help            show this help message and exit
  -b BRANCH, --branch BRANCH
                        Branch to push the changes to
  -u USERNAME, --username USERNAME
                        Git username if Basic Auth should be used
  -p PASSWORD, --password PASSWORD
                        Git password if Basic Auth should be used
  -j GIT_USER, --git-user GIT_USER
                        Git Username
  -e GIT_EMAIL, --git-email GIT_EMAIL
                        Git User Email
  -c [CREATE_PR], --create-pr [CREATE_PR]
                        Creates a Pull Request (only when --branch is not
                        master/default branch)
  -a [AUTO_MERGE], --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  -o ORGANISATION, --organisation ORGANISATION
                        Apps Git organisation/projectKey
  -n REPOSITORY_NAME, --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  -s GIT_PROVIDER, --git-provider GIT_PROVIDER
                        Git server provider
  -w GIT_PROVIDER_URL, --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
```


## Screenshots

![Example PR Overview](/doc/example_pr_overview.png?raw=true "Example of a created PR")
![Example PR Diff](/doc/example_pr_diff.png?raw=true "Example of a PR yaml file diff")

## Contributing

### Installation (dev)

```bash
$ make install
```

### General

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)

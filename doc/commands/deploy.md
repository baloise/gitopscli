[GitOps CLI](../../README.md) » deploy

# deploy
```
usage: gitopscli deploy [-h] -f FILE -v VALUES [-g [SINGLE_COMMIT]] -u
                        USERNAME -p PASSWORD [-j GIT_USER] [-e GIT_EMAIL] -o
                        ORGANISATION -n REPOSITORY_NAME [-s GIT_PROVIDER]
                        [-w GIT_PROVIDER_URL] [-b BRANCH] [-c [CREATE_PR]]
                        [-a [AUTO_MERGE]]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  YAML file path
  -v VALUES, --values VALUES
                        YAML/JSON object with the YAML path as key and the
                        desired value as value
  -g [SINGLE_COMMIT], --single-commit [SINGLE_COMMIT]
                        Create only single commit for all updates
  -u USERNAME, --username USERNAME
                        Git username
  -p PASSWORD, --password PASSWORD
                        Git password or token
  -j GIT_USER, --git-user GIT_USER
                        Git Username
  -e GIT_EMAIL, --git-email GIT_EMAIL
                        Git User Email
  -o ORGANISATION, --organisation ORGANISATION
                        Apps Git organisation/projectKey
  -n REPOSITORY_NAME, --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  -s GIT_PROVIDER, --git-provider GIT_PROVIDER
                        Git server provider
  -w GIT_PROVIDER_URL, --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  -b BRANCH, --branch BRANCH
                        Branch to push the changes to
  -c [CREATE_PR], --create-pr [CREATE_PR]
                        Creates a Pull Request (only when --branch is not
                        master/default branch)
  -a [AUTO_MERGE], --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
```

## Example
```bash
gitopscli deploy \
--git-provider-url https://bitbucket.baloise.dev \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "deployment" \
--repository-name "incubator-non-prod" \
--file example/values.yaml \
--branch deploy-$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 5 | head -n 1) \
--values "{image.tag: v0.3.0}" \
--create-pr \
--auto-merge
```

## Screenshots
![Example PR Overview](/doc/screenshots/example_pr_overview.png?raw=true "Example of a created PR")
![Example PR Diff](/doc/screenshots/example_pr_diff.png?raw=true "Example of a PR yaml file diff")
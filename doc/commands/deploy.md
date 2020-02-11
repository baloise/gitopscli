[GitOps CLI](../../README.md) » deploy

# deploy
```
usage: gitopscli deploy [-h] --file FILE --values VALUES
                        [--single-commit [SINGLE_COMMIT]] --username USERNAME
                        --password PASSWORD [--git-user GIT_USER]
                        [--git-email GIT_EMAIL] --organisation ORGANISATION
                        --repository-name REPOSITORY_NAME
                        [--git-provider GIT_PROVIDER]
                        [--git-provider-url GIT_PROVIDER_URL]
                        [--branch BRANCH] [--create-pr [CREATE_PR]]
                        [--auto-merge [AUTO_MERGE]] [-v [VERBOSE]]

optional arguments:
  -h, --help            show this help message and exit
  --file FILE           YAML file path
  --values VALUES       YAML/JSON object with the YAML path as key and the
                        desired value as value
  --single-commit [SINGLE_COMMIT]
                        Create only single commit for all updates
  --username USERNAME   Git username
  --password PASSWORD   Git password or token
  --git-user GIT_USER   Git Username
  --git-email GIT_EMAIL
                        Git User Email
  --organisation ORGANISATION
                        Apps Git organisation/projectKey
  --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  --git-provider GIT_PROVIDER
                        Git server provider
  --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  --branch BRANCH       Branch to push the changes to
  --create-pr [CREATE_PR]
                        Creates a Pull Request (only when --branch is not
                        master/default branch)
  --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
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
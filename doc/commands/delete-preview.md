[GitOps CLI](../../README.md) » delete-preview

# delete-preview
```
usage: gitopscli delete-preview [-h] -u USERNAME -p PASSWORD [-j GIT_USER]
                                [-e GIT_EMAIL] -o ORGANISATION -n
                                REPOSITORY_NAME [-s GIT_PROVIDER]
                                [-w GIT_PROVIDER_URL] [-b BRANCH]
                                [-c [CREATE_PR]] [-a [AUTO_MERGE]]

optional arguments:
  -h, --help            show this help message and exit
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
gitopscli delete-preview \
--git-provider-url https://bitbucket.baloise.dev \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "my-team" \
--repository-name "my-app" \
--branch "some-branch-name" \
--create-pr \
--auto-merge
```

## .gitops.config.yaml
Make sure that your application repository contains a `.gitops.config.yaml` file.

```yaml
deploymentConfig:
  # The organisation name of your deployment repo
  org: DPL
  # The repostiory name of your deployment repo
  repository: incubator-non-prod
  # The name of the application that is used in your deployment repo
  applicationName: example

previewConfig:
  route:
    host:
      # your router host.
      #{SHA256_8CHAR_BRANCH_HASH} gets replaced by a shortened hash of your feature branch name
      template: example-{SHA256_8CHAR_BRANCH_HASH}.example.tld
  replace:
    # Paths that should be replaced
    - path: image.tag
      variable: GIT_COMMIT # this is the latest git hash of the PR branch
    - path: route.host
      variable: ROUTE_HOST # this is the resolved SHA256_8CHAR_BRANCH_HASH from above

```

# delete-pr-preview

The `delete-pr-preview` command can be used to delete a preview previously created with the [`create-pr-preview` command](/gitopscli/commands/create-pr-preview/). Please refer to `create-pr-preview` documentation for the needed configuration files.

## Example

```bash
gitopscli delete-pr-preview \
  --git-provider-url https://bitbucket.baloise.dev \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "my-team" \
  --repository-name "app-xy" \
  --branch "my-pr-branch" \
```

## Usage
```
usage: gitopscli delete-pr-preview [-h] --username USERNAME --password
                                   PASSWORD [--git-user GIT_USER]
                                   [--git-email GIT_EMAIL] --organisation
                                   ORGANISATION --repository-name
                                   REPOSITORY_NAME
                                   [--git-provider GIT_PROVIDER]
                                   [--git-provider-url GIT_PROVIDER_URL]
                                   --branch BRANCH
                                   [--expect-preview-exists [EXPECT_PREVIEW_EXISTS]]
                                   [-v [VERBOSE]]

options:
  -h, --help            show this help message and exit
  --username USERNAME   Git username (alternative: GITOPSCLI_USERNAME env
                        variable)
  --password PASSWORD   Git password or token (alternative: GITOPSCLI_PASSWORD
                        env variable)
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
  --branch BRANCH       The branch for which the preview was created for
  --expect-preview-exists [EXPECT_PREVIEW_EXISTS]
                        Fail if preview does not exist
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
```
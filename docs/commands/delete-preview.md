# delete-preview

The `delete-preview` command can be used to delete a preview previously created with the [`create-preview` command](/gitopscli/commands/create-preview/). Please refer to `create-preview` documentation for the needed configuration files.

## Example

```bash
gitopscli delete-preview \
  --git-provider-url https://bitbucket.baloise.dev \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "my-team" \
  --repository-name "app-xy" \
  --preview-id "test123" \
```

## Usage
```
usage: gitopscli delete-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL]
                                --preview-id PREVIEW_ID
                                [--expect-preview-exists [EXPECT_PREVIEW_EXISTS]]
                                [-v [VERBOSE]]

optional arguments:
  -h, --help            show this help message and exit
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
  --preview-id PREVIEW_ID
                        The user-defined preview ID
  --expect-preview-exists [EXPECT_PREVIEW_EXISTS]
                        Fail if preview does not exist
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
```
# create-pr-preview

The `create-pr-preview` command can be used to create a preview environment in your *deployment config repository* for a pull request of your *app repository*. You can later easily delete this preview with the [`delete-pr-preview` command](/gitopscli/commands/delete-pr-preview/).

You need to provide some additional configuration files in your repositories for this command to work. 

{!preview-configuration.md!}

## Example

```bash
gitopscli create-pr-preview \
  --git-provider-url https://bitbucket.baloise.dev \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "my-team" \
  --repository-name "app-xy" \
  --pr-id 4711
```

## Usage
```
usage: gitopscli create-pr-preview [-h] --username USERNAME --password
                                   PASSWORD [--git-user GIT_USER]
                                   [--git-email GIT_EMAIL]
                                   [--git-author-name GIT_AUTHOR_NAME]
                                   [--git-author-email GIT_AUTHOR_EMAIL]
                                   --organisation ORGANISATION
                                   --repository-name REPOSITORY_NAME
                                   [--git-provider GIT_PROVIDER]
                                   [--git-provider-url GIT_PROVIDER_URL]
                                   --pr-id PR_ID [--parent-id PARENT_ID]
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
  --git-author-name GIT_AUTHOR_NAME
                        Git Author Name
  --git-author-email GIT_AUTHOR_EMAIL
                        Git Author Email
  --organisation ORGANISATION
                        Apps Git organisation/projectKey
  --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  --git-provider GIT_PROVIDER
                        Git server provider
  --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  --pr-id PR_ID         the id of the pull request
  --parent-id PARENT_ID
                        the id of the parent comment, in case of a reply
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
```

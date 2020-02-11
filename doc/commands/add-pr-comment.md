[GitOps CLI](../../README.md) » add-pr-comment

# add-pr-comment
```
usage: gitopscli add-pr-comment [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL] --pr-id
                                PR_ID [--parent-id PARENT_ID] [-v [VERBOSE]]
                                --text TEXT

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
  --pr-id PR_ID         the id of the pull request
  --parent-id PARENT_ID
                        the id of the parent comment, in case of a reply
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
  --text TEXT           the text of the comment
```

## Example
```bash
gitopscli add-pr-comment \
--git-provider-url https://bitbucket.baloise.dev \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "my-team" \
--repository-name "my-app" \
--pr-id 4711 \
--text "this is a comment" 
```
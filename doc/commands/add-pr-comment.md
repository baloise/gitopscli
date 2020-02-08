[GitOps CLI](../../README.md) » add-pr-comment

# add-pr-comment
```
usage: gitopscli add-pr-comment [-h] [-u USERNAME] [-p PASSWORD]
                                [-j GIT_USER] [-e GIT_EMAIL]
                                -o ORGANISATION -n REPOSITORY_NAME [-s GIT_PROVIDER]
                                [-w GIT_PROVIDER_URL] -i PR_ID [-x PARENT_ID]
                                -t TEXT

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Git username if Basic Auth should be used
  -p PASSWORD, --password PASSWORD
                        Git password if Basic Auth should be used
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
  -i PR_ID, --pr-id PR_ID
                        the id of the pull request
  -x PARENT_ID, --parent-id PARENT_ID
                        the id of the parent comment, in case of a reply
  -t TEXT, --text TEXT  the text of the comment
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
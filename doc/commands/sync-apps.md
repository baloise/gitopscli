[GitOps CLI](../../README.md) » sync-apps

# sync-apps
```
usage: gitopscli sync-apps [-h] [-u USERNAME] [-p PASSWORD]
                           [-j GIT_USER] [-e GIT_EMAIL]
                           -o ORGANISATION -n REPOSITORY_NAME [-s GIT_PROVIDER]
                           [-w GIT_PROVIDER_URL] -i ROOT_ORGANISATION -r
                           ROOT_REPOSITORY_NAME

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
  -i ROOT_ORGANISATION, --root-organisation ROOT_ORGANISATION
                        Apps config repository organisation
  -r ROOT_REPOSITORY_NAME, --root-repository-name ROOT_REPOSITORY_NAME
                        Root config repository organisation
```

## Example
```bash
gitopscli sync-apps --git-provider-url https://bitbucket.baloise.dev \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "my-team" \
--repository-name "my-app" \
--root-organisation "deployment" \
--root-repository-name "apps-root-config" 
```

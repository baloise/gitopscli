# sync-apps
```
usage: gitopscli sync-apps [-h] --username USERNAME --password PASSWORD
                           [--git-user GIT_USER] [--git-email GIT_EMAIL]
                           --organisation ORGANISATION --repository-name
                           REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                           [--git-provider-url GIT_PROVIDER_URL]
                           [-v [VERBOSE]] --root-organisation
                           ROOT_ORGANISATION --root-repository-name
                           ROOT_REPOSITORY_NAME

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
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
  --root-organisation ROOT_ORGANISATION
                        Apps config repository organisation
  --root-repository-name ROOT_REPOSITORY_NAME
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

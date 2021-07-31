# create-preview

The `create-preview` command can be used to create a preview environment in your *deployment config repository* for a commit hash of your *app repository*. You can later easily delete this preview with the [`delete-preview` command](/gitopscli/commands/delete-preview/).

You need to provide some additional configuration files in your repositories for this command to work. 

{!preview-configuration.md!}

## Returned Information

After running this command you'll find a YAML file at `/tmp/gitopscli-preview-info.yaml`. It contains generated information about your preview environment:

```yaml
previewId: PREVIEW_ID
previewIdHash: 685912d3
routeHost: app.xy-685912d3.example.tld
namespace: my-app-685912d3-preview
```

## Example

```bash
gitopscli create-preview \
  --git-provider-url https://bitbucket.baloise.dev \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "my-team" \
  --repository-name "app-xy" \
  --git-hash "c0784a34e834117e1489973327ff4ff3c2582b94" \
  --preview-id "test-preview-id" \
```

## Usage
```
usage: gitopscli create-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL]
                                --preview-id PREVIEW_ID
                                [-v [VERBOSE]]

optional arguments:
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
  --git-hash GIT_HASH   the git hash which should be deployed
  --preview-id PREVIEW_ID
                        The user-defined preview ID
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
```

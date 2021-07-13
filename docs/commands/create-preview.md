# create-preview

The `create-preview` command can be used to create a preview environment in your *deployment config repository* for a commit hash of your *app repository*. You can later easily delete this preview with the [`delete-preview` command](/gitopscli/commands/delete-preview/).

You need to provide some additional configuration files in your repositories for this command to work. 

## Configuration
### Preview Templates

You have to provide a folder with the deployment configuration templates for every application you want to use this command for. By default it is assumed that this folder is located in your *deployment config repository* under the top-level folder `.preview-templates`. For example `.preview-templates/app-xy` for your app `app-xy`. The `create-preview` command simply copies this directory to the root of your *deployment config repository* and replaces e.g. image tag and route host which are specific to this preview.

```
deployment-config-repo/
├── .preview-templates
│   └── app-xy                        <- Can contain any files and folders
│       ├── values.yaml
│       └── some-more-config-files-or-folders
├── app-xy-production
├── app-xy-staging
├── app-xy-test
└── app-xy-my-branch-c7003101-preview  <- This is how a created preview looks by default
    ├── values.yaml                    <- e.g. image tag and route host are replaced in this one
    └── some-more-config-files-or-folders
```

### .gitops.config.yaml

Make sure that your *app repository* contains a `.gitops.config.yaml` file. This file provides all information to 

1. find repository, branch, and folder containing the template
2. templates for host and namespace name
3. replacements in template files
4. find repository and branch where the preview should be created (i.e. your *deployment config repository*)

```yaml
apiVersion: v1
applicationName: app-xy
previewConfig:
  host: {PREVIEW_NAMESPACE}.example.tld
# template:                              # optional section
#   organisation: templates              # optional (default: target.organisation)
#   repository: template-repo            # optional (default: target.repository)
#   branch: master                       # optional (default: target.branch)
#   path: custom/{APPLICATION_NAME}      # optional (default: '.preview-templates/{APPLICATION_NAME}')
  target:
    organisation: deployments
    repository: deployment-config-repo
#   branch: master                       # optional (defaults to repo's default branch)
    namespace: {APPLICATION_NAME}-{PREVIEW_ID_HASH}-preview  # optional (default: '{APPLICATION_NAME}-{PREVIEW_ID}-{PREVIEW_ID_HASH}-preview',
                                                             #           Invalid characters in PREVIEW_ID will be replaced. PREVIEW_ID will be
                                                             #           truncated if max namespace length exceeds 63 chars.)
  replace:
    Chart.yaml:
      - path: name
        value: {PREVIEW_NAMESPACE}
    values.yaml:
      - path: app.image
        value: registry.example.tld/my-app:{GIT_HASH}
      - path: route.host
        value: {PREVIEW_HOST}
```

#### Variables
- `APPLICATION_NAME`: value from `applicationName`
- `GIT_HASH`: The CLI provided `--git-hash`
- `PREVIEW_ID`: The CLI provided `--preview-id`
- `PREVIEW_ID_HASH`: The first 8 characters of the SHA256 hash of `PREVIEW_ID`
- `PREVIEW_NAMESPACE`: The resulting value of `previewConfig.target.namespace`
- `PREVIEW_HOST`: The resulting value of `previewConfig.host`

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

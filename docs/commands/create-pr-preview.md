# create-pr-preview

The `create-pr-preview` command can be used to create a preview environment in your *deployment config repository* for a pull request of your *app repository*. You can later easily delete this preview with the [`delete-pr-preview` command](/gitopscli/commands/delete-pr-preview/).

You need to provide some additional configuration files in your repositories for this command to work. 

## Configuration
### Preview Templates

Your *deployment config repository* needs to contain a `.preview-templates` folder with the deployment configuration templates for every application you want to use this command for.

For example you have to provide `.preview-templates/app-xy` for your app `app-xy`. The `create-pr-preview` command simply copies this directory to the root of the repository. Only image tag and route host will be replaced in the preview version of the deployment.

```
deployment-config-repo/
├── .preview-templates
│   └── app-xy
│       ├── values.yaml
│       └── some-more-config-files-or-folders
├── app-xy-production
├── app-xy-staging
├── app-xy-test
└── app-xy-c7003101-preview  <- This is how a created preview looks like
    ├── values.yaml          <- image tag and route host are replaced in this one
    └── some-more-config-files-or-folders
```

!!! info "Currently you have to specify image tag and route host in a `values.yaml` file. We are working on making this configurable in the future."

### .gitops.config.yaml

Make sure that your *app repository* contains a `.gitops.config.yaml` file. This file provides all information to 

1. find the *deployment config repository*
2. locate the preview template for your app
3. replace image tag and route host in the template

```yaml
deploymentConfig:
  # The organisation name of your deployment repo
  org: deployments
  # The repostiory name of your deployment repo
  repository: deployment-config-repo
  # The name of the application (name of the folder in `.preview-templates`)
  applicationName: app-xy

previewConfig:
  route:
    host:
      # Your router host
      # {SHA256_8CHAR_BRANCH_HASH} gets replaced by a shortened hash of your feature branch name
      template: app.xy-{SHA256_8CHAR_BRANCH_HASH}.example.tld
  replace:
    # Paths that should be replaced in the `values.yaml`
    - path: image.tag
      variable: GIT_COMMIT # this is the latest git hash of the pull request branch
    - path: route.host
      variable: ROUTE_HOST # this is the resolved host.template from above
```

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
usage: gitopscli create-pr-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL]
                                --pr-id PR_ID
                                [--parent-id PARENT_ID] [-v [VERBOSE]]

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
```

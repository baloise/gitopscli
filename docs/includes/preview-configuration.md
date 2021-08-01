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
3. replace values in template files
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
- `GIT_HASH`:
    - `create-preview`: The CLI provided `--git-hash`
    - `create-pr-preview`: The git hash of the *app repository* commit that will be deployed
- `PREVIEW_ID`:
    - `create-preview`: The CLI provided `--preview-id`
    - `create-pr-preview`: The branch name in the *app repository*
- `PREVIEW_ID_HASH`: The first 8 characters of the SHA256 hash of `PREVIEW_ID`
- `PREVIEW_NAMESPACE`: The resulting value of `previewConfig.target.namespace`
- `PREVIEW_HOST`: The resulting value of `previewConfig.host`

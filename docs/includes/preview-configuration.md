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
3. replace values in template files (see [`deploy` command](/gitopscli/commands/deploy/) for details on the key syntax)
4. find repository and branch where the preview should be created (i.e. your *deployment config repository*)
5. message templates used to comment your pull request

```yaml
apiVersion: v2
applicationName: app-xy
# messages:                              # optional section
#   previewEnvCreated: "Created preview at revision ${GIT_HASH}. You can access it here: https://${PREVIEW_HOST}/some-fancy-path"    # optional (default: "New preview environment created for version `${GIT_HASH}`. Access it here: https://${PREVIEW_HOST}")
#   previewEnvUpdated: "Updated preview to revision ${GIT_HASH}. You can access it here: https://${PREVIEW_HOST}/some-fancy-path"    # optional (default: "Preview environment updated to version `${GIT_HASH}`. Access it here: https://${PREVIEW_HOST}")
#   previewEnvAlreadyUpToDate: "Your preview is already up-to-date with revision ${GIT-HASH}."                                       # optional (default: "The version `${GIT_HASH}` has already been deployed. Access it here: https://${PREVIEW_HOST}")
previewConfig:
  host: ${PREVIEW_NAMESPACE}.example.tld
# template:                              # optional section
#   organisation: templates              # optional (default: target.organisation)
#   repository: template-repo            # optional (default: target.repository)
#   branch: master                       # optional (default: target.branch)
#   path: custom/${APPLICATION_NAME}     # optional (default: '.preview-templates/${APPLICATION_NAME}')
  target:
    organisation: deployments
    repository: deployment-config-repo
#   branch: master                       # optional (defaults to repo's default branch)
#   namespace: ${APPLICATION_NAME}-${PREVIEW_ID_HASH}-preview'  # optional (default: '${APPLICATION_NAME}-${PREVIEW_ID}-${PREVIEW_ID_HASH_SHORT}-preview',
                                                                #           Invalid characters in PREVIEW_ID will be replaced. PREVIEW_ID will be
                                                                #           truncated if max namespace length exceeds `maxNamespaceLength` chars.)
#   maxNamespaceLength: 63               # optional (default: 53)
  replace:
    Chart.yaml:
      - path: name
        value: ${PREVIEW_NAMESPACE}
    values.yaml:
      - path: app.image
        value: registry.example.tld/my-app:${GIT_HASH}
      - path: route.host
        value: ${PREVIEW_HOST}
```

!!! info
    If you currently use the _old_ `.gitops.config.yaml` format (_v0_) you may find this [online converter](https://christiansiegel.github.io/gitopscli-config-converter/) helpful to transition to the current `apiVersion v2`.

    !!! warning
        The _old_ (_v0_) version and `apiVersion v1` are marked deprecated and will be removed in `gitopscli` version 6.0.0.

    Equivalent example:

    ```yaml
    # old 'v0' format
    deploymentConfig:
      org: deployments
      repository: deployment-config-repo
      applicationName: app-xy
    previewConfig:
      route:
        host:
          template: app-xy-{SHA256_8CHAR_BRANCH_HASH}.example.tld
      replace:
        - path: image.tag
          variable: GIT_COMMIT
        - path: route.host
          variable: ROUTE_HOST
    ```

    ```yaml
    # v2 format
    apiVersion: v2
    applicationName: app-xy
    previewConfig:
      host: ${PREVIEW_NAMESPACE}.example.tld
      target:
        organisation: deployments
        repository: deployment-config-repo
        namespace: ${APPLICATION_NAME}-${PREVIEW_ID_HASH}-preview
      replace:
        Chart.yaml:
          - path: name
            value: ${PREVIEW_NAMESPACE}
        values.yaml:
          - path: image.tag
            value: ${GIT_HASH}
          - path: route.host
            value: ${PREVIEW_HOST}
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
- `PREVIEW_ID_HASH_SHORT`: The first 3 characters of the SHA256 hash of `PREVIEW_ID`
- `PREVIEW_NAMESPACE`: The resulting value of `previewConfig.target.namespace`
- `PREVIEW_HOST`: The resulting value of `previewConfig.host`

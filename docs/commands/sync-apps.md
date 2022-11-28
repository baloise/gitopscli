# sync-apps

The `sync-apps` command can be used to keep a *root config repository* in sync with several *app config repositories*. You can use this command if your config repositories are structured in the following (opinionated) way:

## Repository Structure

### App Config Repositories

You have `1..n` config repositories for the deployment configurations of your applications (e.g. one per team). Every *app config repository* can contain `0..n` directories (e.g. containing [Helm](https://helm.sh/) charts). Directories starting with a dot will be ignored. Example:

```
team-1-app-config-repo/
├── .this-will-be-ignored
├── app-xy-production
├── app-xy-staging
└── app-xy-test
```

### Root Config Repository

The *root config repository* acts as a single entrypoint for your GitOps continous delivery tool (e.g. [Argo CD](https://argoproj.github.io/argo-cd/)). Here you define all applications in your cluster and link to the *app config repositories* with their deployment configurations. It is structured in the following way:

```
root-config-repo/
├── apps
│   ├── team-a.yaml
│   └── team-b.yaml
└── bootstrap
    └── values.yaml
```

**bootstrap/values.yaml**
```yaml
bootstrap:
  - name: team-a # <- every entry links to a YAML file in the `apps/` directory
  - name: team-b
```
Alternative, when using a Chart as dependency with an alias 'config':
```yaml
config:
  bootstrap:
   - name: team-a # <- every entry links to a YAML file in the `apps/` directory
   - name: team-b
```

**apps/team-a.yaml**
```yaml
repository: https://github.com/company-deployments/team-1-app-config-repo.git # link to your apps root repository

# The applications that are synced by the `sync-app` command:
applications:
  app-xy-production: # <- every entry corresponds to a directory in the apps root repository
  app-xy-staging:
  app-xy-test:
```
or

```yaml
config:
  repository: https://github.com/company-deployments/team-1-app-config-repo.git # link to your apps root repository

# The applications that are synced by the `sync-app` command:
  applications:
   app-xy-production: # <- every entry corresponds to a directory in the apps root repository
   app-xy-staging:
   app-xy-test:
```

## Example

```bash
gitopscli sync-apps \
  --git-provider-url github \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "company-deployments" \
  --repository-name "team-1-app-config-repo" \
  --root-organisation "company-deployments" \
  --root-repository-name "root-config-repo"
```

## Usage
```
usage: gitopscli sync-apps [-h] --username USERNAME --password PASSWORD
                           [--git-user GIT_USER] [--git-email GIT_EMAIL]
                           --organisation ORGANISATION --repository-name
                           REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                           [--git-provider-url GIT_PROVIDER_URL]
                           [-v [VERBOSE]] --root-organisation
                           ROOT_ORGANISATION --root-repository-name
                           ROOT_REPOSITORY_NAME

options:
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
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
  --root-organisation ROOT_ORGANISATION
                        Root config repository organisation
  --root-repository-name ROOT_REPOSITORY_NAME
                        Root config repository name
```

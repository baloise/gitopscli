# deploy

The `deploy` command can be used to deploy applications by updating the image tags in the YAML files of a config repository. Of course, you can also use it to update any YAML values in a git repository. However, only _one_ YAML can be changed at a time.

## Example
Let's assume you have a repository `deployment/myapp-non-prod` which contains your deployment configuration in the form of YAML files (e.g. [Helm](https://helm.sh/) charts). To deploy a new version of your application you need to update some values in `example/values.yaml`.

```yaml
# Example Helm values.yaml
frontend:
  repository: my-app/frontend
  tag: 1.0.0 # <- you want to change this value
backend:
  repository: my-app/backend
  tag: 1.0.0 # <- and this one
  env:
  - name: TEST
    value: foo # <- and this one in a list, selected via sibling value 'TEST'
```

With the following command GitOps CLI will update all values on the default branch.

```bash
gitopscli deploy \
  --git-provider-url https://bitbucket.baloise.dev \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "deployment" \
  --repository-name "myapp-non-prod" \
  --file "example/values.yaml" \
  --values "{frontend.tag: 1.1.0, backend.tag: 1.1.0, 'backend.env[?name==''TEST''].value': bar}"
```

You could also use the list index to replace the latter (`my-app.env.[0].value`). For more details on the underlying *JSONPath* syntax, please refer to the [documenatation of the used library *jsonpath-ng*](https://github.com/h2non/jsonpath-ng#jsonpath-syntax).

### Number Of Commits

Note that by default GitOps CLI will create a separate commit for every value change:

```
commit 0dcaa136b4c5249576bb1f40b942bff6ac718144
Author: GitOpsCLI <gitopscli@baloise.dev>
Date:   Thu Mar 12 15:30:32 2020 +0100

    changed 'backend.env[?name=='TEST'].value' to 'bar' in example/values.yaml

commit d98913ad8fecf571d5f8c3635f8070b05c43a9ca
Author: GitOpsCLI <gitopscli@baloise.dev>
Date:   Thu Mar 12 15:30:32 2020 +0100

    changed 'backend.tag' to '1.1.0' in example/values.yaml

commit 649bc72fe798891244c11809afc9fae83309772a
Author: GitOpsCLI <gitopscli@baloise.dev>
Date:   Thu Mar 12 15:30:32 2020 +0100

    changed 'frontend.tag' to '1.1.0' in example/values.yaml
```

If you prefer to create a single commit for all changes add `--single-commit` to the command:

```
commit 3b96839e90c35b8decf89f34a65ab6d66c8bab28
Author: GitOpsCLI <gitopscli@baloise.dev>
Date:   Thu Mar 12 15:30:00 2020 +0100

    updated 3 values in example/values.yaml

    frontend.tag: '1.1.0'
    backend.tag: '1.1.0'
    'backend.env[?name==''TEST''].value': 'bar'
```

### Specific Commit Message

If you want to specify the commit message of the deployment then you can use the following param:

`--commit-message`

```bash
gitopscli deploy \
  --git-provider-url https://bitbucket.baloise.dev \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "deployment" \
  --repository-name "myapp-non-prod" \
  --commit-message "test commit message" \
  --file "example/values.yaml" \
  --values "{frontend.tag: 1.1.0, backend.tag: 1.1.0, 'backend.env[?name==''TEST''].value': bar}"
```

This will end up in one single commit with your specified commit-message.

### Create Pull Request

In some cases you might want to create a pull request for your updates. You can achieve this by adding `--create-pr` to the command. The pull request can be left open or merged directly with `--auto-merge`.

```bash
gitopscli deploy \
  --git-provider-url https://bitbucket.baloise.dev \
  --username $GIT_USERNAME \
  --password $GIT_PASSWORD \
  --git-user "GitOps CLI" \
  --git-email "gitopscli@baloise.dev" \
  --organisation "deployment" \
  --repository-name "myapp-non-prod" \
  --file "example/values.yaml" \
  --values "{frontend.tag: 1.1.0, backend.tag: 1.1.0, 'backend.env[?name==''TEST''].value': bar}" \
  --create-pr \
  --auto-merge
```

![Example PR Overview](../assets/images/screenshots/example-pr-overview.png?raw=true "Example of the created PR")
![Example PR Diff](../assets/images/screenshots/example-pr-diff.png?raw=true "Example of the PR file diff")
![Example PR Commits](../assets/images/screenshots/example-pr-commits.png?raw=true "Example of a PR commits")


## Usage
```
usage: gitopscli deploy [-h] --file FILE --values VALUES
                        [--single-commit [SINGLE_COMMIT]]
                        [--commit-message COMMIT_MESSAGE] --username USERNAME
                        --password PASSWORD [--git-user GIT_USER]
                        [--git-email GIT_EMAIL] --organisation ORGANISATION
                        --repository-name REPOSITORY_NAME
                        [--git-provider GIT_PROVIDER]
                        [--git-provider-url GIT_PROVIDER_URL]
                        [--create-pr [CREATE_PR]] [--auto-merge [AUTO_MERGE]]
                        [--merge-method MERGE_METHOD] [-v [VERBOSE]]

options:
  -h, --help            show this help message and exit
  --file FILE           YAML file path
  --values VALUES       YAML/JSON object with the YAML path as key and the desired value as value
  --single-commit [SINGLE_COMMIT]
                        Create only single commit for all updates
  --commit-message COMMIT_MESSAGE
                        Specify exact commit message of deployment commit
  --username USERNAME   Git username (alternative: GITOPSCLI_USERNAME env variable)
  --password PASSWORD   Git password or token (alternative: GITOPSCLI_PASSWORD env variable)
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
                        Git provider base API URL (e.g. https://bitbucket.example.tld)
  --create-pr [CREATE_PR]
                        Creates a Pull Request
  --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with --create-pr)
  --merge-method MERGE_METHOD
                        Merge Method (e.g., 'squash', 'rebase', 'merge') (default: merge)
  --json [JSON]         Print a JSON object containing deployment information
  --pr-labels PR_LABELS
                        JSON array pr labels (Gitlab, Github supported)
  --merge-parameters MERGE_PARAMETERS
                        JSON object pr parameters (only Gitlab supported)
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging

```

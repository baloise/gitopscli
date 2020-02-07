[GitOps CLI](../../README.md) » create-preview

# create-preview
```
usage: gitopscli create-preview [-h] [-b BRANCH] [-u USERNAME] [-p PASSWORD]
                                [-j GIT_USER] [-e GIT_EMAIL] [-c [CREATE_PR]]
                                [-a [AUTO_MERGE]] -o ORGANISATION -n
                                REPOSITORY_NAME [-s GIT_PROVIDER]
                                [-w GIT_PROVIDER_URL] -i PR_ID [-x PARENT_ID]

optional arguments:
  -h, --help            show this help message and exit
  -b BRANCH, --branch BRANCH
                        Branch to push the changes to
  -u USERNAME, --username USERNAME
                        Git username if Basic Auth should be used
  -p PASSWORD, --password PASSWORD
                        Git password if Basic Auth should be used
  -j GIT_USER, --git-user GIT_USER
                        Git Username
  -e GIT_EMAIL, --git-email GIT_EMAIL
                        Git User Email
  -c [CREATE_PR], --create-pr [CREATE_PR]
                        Creates a Pull Request (only when --branch is not
                        master/default branch)
  -a [AUTO_MERGE], --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
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
```

## Example
```bash
gitopscli create-preview \
--git-provider-url https://bitbucket.baloise.dev \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--git-user "GitOpsCLI" \
--git-email "gitopscli@baloise.dev" \
--organisation "my-team" \
--repository-name "my-app" \
--branch "some-branch-name" \
--create-pr \
--pr-id 4711 \
--auto-merge
```

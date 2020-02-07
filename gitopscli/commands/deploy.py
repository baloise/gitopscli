import json
import os
import shutil
import uuid

from gitopscli.git.create_git import create_git
from gitopscli.yaml.yaml_util import update_yaml_file


def deploy(
    command,
    file,
    values,
    branch,
    username,
    password,
    git_user,
    git_email,
    create_pr,
    auto_merge,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "deploy"

    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)

    try:
        git = create_git(
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            tmp_dir,
        )
        git.checkout("master")
        git.new_branch(branch)
        full_file_path = git.get_full_file_path(file)
        for key in values:
            value = values[key]
            update_yaml_file(full_file_path, key, value)
            git.commit(f"changed '{key}' to '{value}'")

        git.push(branch)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if create_pr and branch != "master":
        title = f"Updated values in {file}"
        description = f"""
This Pull Request is automatically created through [gitopscli](https://github.com/baloise-incubator/gitopscli).
Files changed: `{file}`
Values changed:
```json
{json.dumps(values)}
```
"""
        pull_request = git.create_pull_request(branch, "master", title, description)
        print(f"Pull request created: {git.get_pull_request_url(pull_request)}")

        if auto_merge:
            git.merge_pull_request(pull_request)
            print("Pull request merged")

            git.delete_branch(branch)
            print(f"Branch '{branch}' deleted")

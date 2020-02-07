import json
import logging
import os
import shutil
import uuid

from gitopscli.git.create_git import create_git
from gitopscli.yaml.yaml_util import update_yaml_file


def deploy_command(
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
    logging.info("Created directory %s", tmp_dir)

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
        logging.info("Master checkout successful")
        git.new_branch(branch)
        logging.info("Created branch %s", branch)
        full_file_path = git.get_full_file_path(file)
        updated_any_value = False
        for key in values:
            value = values[key]
            if not update_yaml_file(full_file_path, key, value):
                logging.info("Yaml property %s already up-to-date", key)
                continue
            logging.info("Updated yaml property %s to %s", key, value)
            updated_any_value = True

            git.commit(f"changed '{key}' to '{value}'")

        if not updated_any_value:
            logging.info("All values already up-to-date. I'm done here")
            return

        git.push(branch)
        logging.info("Pushed branch %s", branch)
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
        logging.info("Pull request created: %s", {git.get_pull_request_url(pull_request)})

        if auto_merge:
            git.merge_pull_request(pull_request)
            logging.info("Pull request merged")

            git.delete_branch(branch)
            logging.info("Branch '%s' deleted", branch)

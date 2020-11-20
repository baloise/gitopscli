import logging
import os
import uuid

from gitopscli.git import GitApiConfig, GitRepo, GitRepoApi, GitRepoApiFactory
from gitopscli.io.yaml_util import update_yaml_file, yaml_dump
from gitopscli.gitops_exception import GitOpsException


def deploy_command(
    command,
    file,
    values,
    username,
    password,
    git_user,
    git_email,
    create_pr,
    auto_merge,
    single_commit,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
    commit_message=None,
):
    assert command == "deploy"
    git_api_config = GitApiConfig(username, password, git_provider, git_provider_url,)
    git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name)
    with GitRepo(git_repo_api) as git_repo:
        git_repo.checkout("master")
        logging.info("Master checkout successful")

        config_branch = f"gitopscli-deploy-{str(uuid.uuid4())[:8]}" if create_pr else "master"

        if create_pr:
            git_repo.new_branch(config_branch)
            logging.info("Created branch %s", config_branch)

        updated_values = __update_values(git_repo, git_user, git_email, file, values, single_commit, commit_message)
        if not updated_values:
            logging.info("All values already up-to-date. I'm done here")
            return

        git_repo.push(config_branch)
        logging.info("Pushed branch %s", config_branch)

    if create_pr:
        __create_pr(git_repo_api, config_branch, file, updated_values, auto_merge)


def __update_values(git_repo, git_user, git_email, file, values, single_commit, commit_message):
    full_file_path = git_repo.get_full_file_path(file)
    if not os.path.isfile(full_file_path):
        raise GitOpsException(f"No such file: {file}")

    commit = lambda message: git_repo.commit(git_user, git_email, message)

    updated_values = {}
    for key in values:
        value = values[key]
        try:
            updated_value = update_yaml_file(full_file_path, key, value)
        except KeyError as ex:
            raise GitOpsException(f"Key '{key}' not found in {file}") from ex
        if not updated_value:
            logging.info("Yaml property %s already up-to-date", key)
            continue
        logging.info("Updated yaml property %s to %s", key, value)
        updated_values[key] = value

        if not single_commit and commit_message is None:
            commit(f"changed '{key}' to '{value}' in {file}")

    if updated_values and single_commit and commit_message is None:
        if len(updated_values) == 1:
            key, value = list(updated_values.items())[0]
            commit(f"changed '{key}' to '{value}' in {file}")
        else:
            msg = f"updated {len(updated_values)} value{'s' if len(updated_values) > 1 else ''} in {file}"
            msg += f"\n\n{yaml_dump(updated_values)}"
            commit(msg)

    if updated_values and commit_message is not None:
        commit(commit_message)

    return updated_values


def __create_pr(git_repo_api: GitRepoApi, branch, file, updated_values, auto_merge):
    title = f"Updated values in {file}"
    description = f"""\
Updated {len(updated_values)} value{'s' if len(updated_values) > 1 else ''} in `{file}`:
```yaml
{yaml_dump(updated_values)}
```
"""
    pull_request = git_repo_api.create_pull_request(branch, "master", title, description)
    if auto_merge:
        git_repo_api.merge_pull_request(pull_request.pr_id)
        git_repo_api.delete_branch(branch)

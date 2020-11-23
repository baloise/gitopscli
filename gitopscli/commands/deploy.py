import logging
import os
import uuid
from typing import Any, Callable, Dict, Optional, NamedTuple

from gitopscli.git import GitApiConfig, GitRepo, GitRepoApi, GitRepoApiFactory
from gitopscli.io.yaml_util import update_yaml_file, yaml_dump
from gitopscli.gitops_exception import GitOpsException


class DeployArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    file: str
    values: Any

    single_commit: bool
    commit_message: Optional[str]

    create_pr: bool
    auto_merge: bool


def deploy_command(args: DeployArgs) -> None:
    git_api_config = GitApiConfig(args.username, args.password, args.git_provider, args.git_provider_url,)
    git_repo_api = GitRepoApiFactory.create(git_api_config, args.organisation, args.repository_name)
    with GitRepo(git_repo_api) as git_repo:
        git_repo.checkout("master")

        config_branch = f"gitopscli-deploy-{str(uuid.uuid4())[:8]}" if args.create_pr else "master"

        if args.create_pr:
            git_repo.new_branch(config_branch)

        updated_values = __update_values(git_repo, args)
        if not updated_values:
            logging.info("All values already up-to-date. I'm done here")
            return

        git_repo.push(config_branch)

    if args.create_pr:
        __create_pr(git_repo_api, config_branch, updated_values, args)


def __update_values(git_repo: GitRepo, args: DeployArgs) -> Dict[str, Any]:
    full_file_path = git_repo.get_full_file_path(args.file)
    if not os.path.isfile(full_file_path):
        raise GitOpsException(f"No such file: {args.file}")

    commit: Callable[[str], None] = lambda message: git_repo.commit(args.git_user, args.git_email, message)

    updated_values = {}
    for key in args.values:
        value = args.values[key]
        try:
            updated_value = update_yaml_file(full_file_path, key, value)
        except KeyError as ex:
            raise GitOpsException(f"Key '{key}' not found in {args.file}") from ex
        if not updated_value:
            logging.info("Yaml property %s already up-to-date", key)
            continue
        logging.info("Updated yaml property %s to %s", key, value)
        updated_values[key] = value

        if not args.single_commit and args.commit_message is None:
            commit(f"changed '{key}' to '{value}' in {args.file}")

    if updated_values and args.single_commit and args.commit_message is None:
        if len(updated_values) == 1:
            key, value = list(updated_values.items())[0]
            commit(f"changed '{key}' to '{value}' in {args.file}")
        else:
            msg = f"updated {len(updated_values)} value{'s' if len(updated_values) > 1 else ''} in {args.file}"
            msg += f"\n\n{yaml_dump(updated_values)}"
            commit(msg)

    if updated_values and args.commit_message is not None:
        commit(args.commit_message)

    return updated_values


def __create_pr(git_repo_api: GitRepoApi, branch: str, updated_values: Dict[str, Any], args: DeployArgs) -> None:
    title = f"Updated values in {args.file}"
    description = f"""\
Updated {len(updated_values)} value{'s' if len(updated_values) > 1 else ''} in `{args.file}`:
```yaml
{yaml_dump(updated_values)}
```
"""
    pull_request = git_repo_api.create_pull_request(branch, "master", title, description)
    if args.auto_merge:
        git_repo_api.merge_pull_request(pull_request.pr_id)
        git_repo_api.delete_branch(branch)

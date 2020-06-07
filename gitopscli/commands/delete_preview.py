import hashlib
import logging
import os
import uuid
import shutil

from gitopscli.git.create_git import create_git
from gitopscli.io.gitops_config import GitOpsConfig
from gitopscli.io.tmp_dir import create_tmp_dir, delete_tmp_dir
from gitopscli.gitops_exception import GitOpsException


def delete_preview_command(
    command,
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
    assert command == "delete-preview"

    apps_tmp_dir = create_tmp_dir()
    root_tmp_dir = create_tmp_dir()

    try:
        apps_git = create_git(
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            apps_tmp_dir,
        )

        apps_git.checkout("master")
        logging.info("App repo branch master checkout successful")
        try:
            gitops_config = GitOpsConfig(apps_git.get_full_file_path(".gitops.config.yaml"))
        except FileNotFoundError as ex:
            raise GitOpsException(f"Couldn't find .gitops.config.yaml") from ex
        logging.info("Read GitOpsConfig: %s", gitops_config)

        root_git = create_git(
            username,
            password,
            git_user,
            git_email,
            gitops_config.team_config_org,
            gitops_config.team_config_repo,
            git_provider,
            git_provider_url,
            root_tmp_dir,
        )
        root_git.checkout("master")
        logging.info("Config repo branch master checkout successful")

        if create_pr:
            config_branch = f"gitopscli-delete-preview-{str(uuid.uuid4())[:8]}"
            root_git.new_branch(config_branch)
            logging.info("Created branch %s in config repo", config_branch)
        else:
            config_branch = "master"

        shortened_branch_hash = hashlib.sha256(branch.encode("utf-8")).hexdigest()[:8]
        logging.info("Hashed branch %s to hash: %s", branch, shortened_branch_hash)
        preview_folder_name = gitops_config.application_name + "-" + shortened_branch_hash + "-preview"
        logging.info("Preview folder name: %s", preview_folder_name)
        branch_preview_env_exists = os.path.exists(root_git.get_full_file_path(preview_folder_name))
        logging.info("Is preview env already existing for branch? %s", branch_preview_env_exists)
        if branch_preview_env_exists:
            shutil.rmtree(root_git.get_full_file_path(preview_folder_name), ignore_errors=True)
        else:
            raise GitOpsException(f"There was no preview with name: {preview_folder_name}")
        root_git.commit(f"Delete preview environment for '{gitops_config.application_name}' and branch '{branch}'.")
        root_git.push(config_branch)
        logging.info("Pushed branch %s", config_branch)

    finally:
        delete_tmp_dir(apps_tmp_dir)
        delete_tmp_dir(root_tmp_dir)
    if create_pr:
        pull_request = __create_pullrequest(config_branch, gitops_config, root_git)
        if auto_merge:
            __merge_pullrequest(config_branch, pull_request, root_git)


def __create_pullrequest(branch, gitops_config, root_git):
    title = "Deleted preview environment for " + gitops_config.application_name
    description = f"""
This Pull Request is automatically created through [gitopscli](https://github.com/baloise/gitopscli).
"""
    pull_request = root_git.create_pull_request(branch, "master", title, description)
    logging.info("Pull request created: %s", {root_git.get_pull_request_url(pull_request)})
    return pull_request


def __merge_pullrequest(branch, pull_request, root_git):
    root_git.merge_pull_request(pull_request)
    logging.info("Pull request merged")
    root_git.delete_branch(branch)
    logging.info("Branch '%s' deleted", branch)

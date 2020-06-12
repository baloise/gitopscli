import hashlib
import logging
import os
import shutil
import uuid

from gitopscli.commands import delete_preview_command
from gitopscli.git.create_git import create_git
from gitopscli.yaml.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException


def delete_pr_preview_command(
    command,
    branch,
    username,
    password,
    git_user,
    git_email,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "delete-pr-preview"

    apps_tmp_dir = __create_tmp_dir()
    root_tmp_dir = __create_tmp_dir()

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

        apps_git.checkout(branch)
        git_hash = apps_git.get_last_commit_hash()
        preview_id = hashlib.sha256(branch.encode("utf-8")).hexdigest()[:8]
        logging.info("App repo branch %s checkout successful", branch)
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

        delete_preview_command(
            command,
            git_hash,
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            preview_id
        )

    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)
        shutil.rmtree(root_tmp_dir, ignore_errors=True)

def __create_tmp_dir():
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)
    logging.info("Created directory %s", tmp_dir)
    return tmp_dir

import hashlib
import logging
import os
import shutil
import uuid

from gitopscli.git.create_git import create_git
from gitopscli.yaml.gitops_config import GitOpsConfig
from gitopscli.yaml.yaml_util import update_yaml_file


def create_preview_command(
    command,
    pr_id,
    parent_id,
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
    assert command == "create-preview"

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
        logging.info("App repo branch %s checkout successful", branch)
        shortened_branch_hash = hashlib.sha256(branch.encode("utf-8")).hexdigest()[:8]
        logging.info("Hashed branch %s to hash: %s", branch, shortened_branch_hash)
        gitops_config = GitOpsConfig(apps_git.get_full_file_path(".gitops.config.yaml"))
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
        root_git.new_branch(branch)
        logging.info("Created branch %s in config repo", branch)
        preview_template_folder_name = ".preview-templates/" + gitops_config.application_name
        logging.info("Using the preview template folder: %s", preview_template_folder_name)
        new_preview_folder_name = gitops_config.application_name + "-" + shortened_branch_hash + "-preview"
        logging.info("New folder for preview: %s", new_preview_folder_name)
        route_host = None
        logging.info("New folder for preview: %s", new_preview_folder_name)
        branch_preview_env_already_exist = os.path.exists(root_git.get_full_file_path(new_preview_folder_name))
        logging.info("Is preview env already existing for branch? %s", branch_preview_env_already_exist)
        if gitops_config.route_paths:
            route_host = gitops_config.route_host.replace("previewplaceholder", shortened_branch_hash)
            logging.info("Created route host: %s", route_host)
        if not branch_preview_env_already_exist:
            __create_new_preview_env(
                branch, gitops_config, new_preview_folder_name, preview_template_folder_name, root_git, route_host,
            )
        new_image_tag = apps_git.get_last_commit_hash()
        logging.info("Using image tag from last app repo commit: %s", new_image_tag)
        for image_path in gitops_config.image_paths:
            yaml_replace_path = image_path["yamlpath"]
            logging.info("Replacing property %s with value: %s", yaml_replace_path, new_image_tag)
            update_yaml_file(
                root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"), yaml_replace_path, new_image_tag,
            )
            root_git.commit(f"changed '{yaml_replace_path}' to '{new_image_tag}'")
        root_git.push(branch)
        logging.info("Pushed branch %s", branch)
        pr_comment_text = f"""
Preview created successfully. Access it here: https://{route_host}.
"""
        logging.info("Creating PullRequest comment for pr with id %s and content: %s", pr_id, pr_comment_text)
        apps_git.add_pull_request_comment(pr_id, pr_comment_text, parent_id)
    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)
        shutil.rmtree(root_tmp_dir, ignore_errors=True)
    if create_pr and branch != "master":
        pull_request = __create_pullrequest(branch, gitops_config, root_git)
        if auto_merge:
            __merge_pullrequest(branch, pull_request, root_git)


def __create_new_preview_env(
    branch, gitops_config, new_preview_folder_name, preview_template_folder_name, root_git, route_host,
):
    shutil.copytree(
        root_git.get_full_file_path(preview_template_folder_name), root_git.get_full_file_path(new_preview_folder_name),
    )
    chart_file_path = new_preview_folder_name + "/Chart.yaml"
    logging.info("Looking for Chart.yaml at: %s", chart_file_path)
    if root_git.get_full_file_path(chart_file_path):
        update_yaml_file(root_git.get_full_file_path(chart_file_path), "name", new_preview_folder_name)
        if gitops_config.route_paths:
            for route_path in gitops_config.route_paths:
                yaml_replace_path = route_path["hostpath"]
                logging.info("Replacing property %s with value: %s", yaml_replace_path, route_host)
                update_yaml_file(
                    root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"),
                    yaml_replace_path,
                    route_host,
                )
    root_git.commit(f"Initiated new preview env for branch {branch}'")
    return route_host


def __create_pullrequest(branch, gitops_config, root_git):
    title = "Updated preview environemnt for " + gitops_config.application_name
    description = f"""
This Pull Request is automatically created through [gitopscli](https://github.com/baloise-incubator/gitopscli).
"""
    pull_request = root_git.create_pull_request(branch, "master", title, description)
    logging.info("Pull request created: %s", {root_git.get_pull_request_url(pull_request)})
    return pull_request


def __merge_pullrequest(branch, pull_request, root_git):
    root_git.merge_pull_request(pull_request)
    logging.info("Pull request merged")
    root_git.delete_branch(branch)
    logging.info("Branch '%s' deleted", branch)


def __create_tmp_dir():
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)
    logging.info("Created directory %s", tmp_dir)
    return tmp_dir

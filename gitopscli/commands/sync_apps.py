import logging
import os
import shutil
import uuid

from ruamel.yaml import YAML

from gitopscli.git.create_git import create_git
from gitopscli.yaml.yaml_util import merge_yaml_element
from gitopscli.gitops_exception import GitOpsException


def sync_apps_command(
    command,
    username,
    password,
    git_user,
    git_email,
    root_organisation,
    root_repository_name,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "sync-apps"

    apps_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(apps_tmp_dir)
    logging.info("Created directory %s", apps_tmp_dir)
    root_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(root_tmp_dir)
    logging.info("Created directory %s", root_tmp_dir)

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
        root_git = create_git(
            username,
            password,
            git_user,
            git_email,
            root_organisation,
            root_repository_name,
            git_provider,
            git_provider_url,
            root_tmp_dir,
        )

        __sync_apps(apps_git, root_git)
    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)
        shutil.rmtree(root_tmp_dir, ignore_errors=True)


def __sync_apps(apps_git, root_git):
    repo_apps = __get_repo_apps(apps_git)
    logging.info("Found %s app(s) in %s: %s", len(repo_apps), apps_git.get_clone_url(), ", ".join(repo_apps))

    apps_config_file, app_file_name, apps_from_other_repos = __find_apps_config_from_repo(apps_git, root_git)
    __check_if_app_already_exists(repo_apps, apps_from_other_repos)
    merge_yaml_element(apps_config_file, "applications", dict.fromkeys(repo_apps, {}), True)
    __commit_and_push(apps_git, root_git, app_file_name)


def __find_apps_config_from_repo(apps_git, root_git):
    logging.info("Searching for %s in apps/", apps_git.get_clone_url())
    yaml = YAML()
    # List for all entries in .applications from each config repository
    apps_from_other_repos = []
    found_app_config_file = None
    found_app_config_file_name = None
    app_file_entries = __get_bootstrap_entries(root_git)
    for app_file in app_file_entries:
        app_file_name = "apps/" + app_file["name"] + ".yaml"
        logging.info("Analyzing %s", app_file_name)
        app_config_file = root_git.get_full_file_path(app_file_name)
        with open(app_config_file, "r") as stream:
            app_config_content = yaml.load(stream)
        if app_config_content["repository"] == apps_git.get_clone_url():
            logging.info("Found repository in %s", app_file_name)
            found_app_config_file = app_config_file
            found_app_config_file_name = app_file_name
        else:
            if "applications" in app_config_content and app_config_content["applications"] is not None:
                apps_from_other_repos += app_config_content["applications"].keys()
    if found_app_config_file is None:
        raise GitOpsException(
            f"Could't find config file with .repository={apps_git.get_clone_url()} in apps/ directory"
        )
    return found_app_config_file, found_app_config_file_name, apps_from_other_repos


def __commit_and_push(apps_git, root_git, app_file_name):
    author = apps_git.get_author_from_last_commit()
    root_git.commit(f"{author} updated " + app_file_name)
    root_git.push("master")


def __get_bootstrap_entries(root_git):
    root_git.checkout("master")
    bootstrap_values_file = root_git.get_full_file_path("bootstrap/values.yaml")
    with open(bootstrap_values_file, "r") as stream:
        bootstrap = YAML().load(stream)
    return bootstrap["bootstrap"]


def __get_repo_apps(apps_git):
    apps_git.checkout("master")
    repo_dir = apps_git.get_full_file_path(".")
    return {
        name
        for name in os.listdir(repo_dir)
        if os.path.isdir(os.path.join(repo_dir, name)) and not name.startswith(".")
    }


def __check_if_app_already_exists(apps_dirs, apps_from_other_repos):
    for app_key in apps_dirs:
        if app_key in apps_from_other_repos:
            raise GitOpsException(f"application: {app_key} already exists in a different repository")

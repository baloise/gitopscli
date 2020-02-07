import hashlib
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

    apps_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(apps_tmp_dir)
    root_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(root_tmp_dir)

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
        shortened_branch_hash = str(int(hashlib.sha256(branch.encode("utf-8")).hexdigest(), 16) % 10 ** 8)
        gitops_config = GitOpsConfig(apps_git.get_full_file_path(".gitops.config.yaml"))

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
        root_git.new_branch(branch)
        new_preview_folder_name = gitops_config.application_name + "-" + shortened_branch_hash + "-preview"
        preview_template_folder_name = ".preview-templates/" + gitops_config.application_name
        route_host = None
        if not os.path.exists(root_git.get_full_file_path(new_preview_folder_name)):
            shutil.copytree(
                root_git.get_full_file_path(preview_template_folder_name),
                root_git.get_full_file_path(new_preview_folder_name),
            )
            chart_file_path = new_preview_folder_name + "/Chart.yaml"
            if root_git.get_full_file_path(chart_file_path):
                update_yaml_file(root_git.get_full_file_path(chart_file_path), "name", new_preview_folder_name)
                if gitops_config.route_paths:
                    route_host = gitops_config.route_host.replace("previewplaceholder", shortened_branch_hash)
                    for route_path in gitops_config.route_paths:
                        yaml_replace_path = route_path["hostpath"]
                        update_yaml_file(
                            root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"),
                            yaml_replace_path,
                            route_host,
                        )

            root_git.commit(f"Initiated new preview env for branch {branch}'")

        new_image_tag = apps_git.get_last_commit_hash()
        for image_path in gitops_config.image_paths:
            yaml_replace_path = image_path["yamlpath"]
            update_yaml_file(
                root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"), yaml_replace_path, new_image_tag,
            )
            root_git.commit(f"changed '{yaml_replace_path}' to '{new_image_tag}'")

        root_git.push(branch)
        pr_comment_text = f"""
Preview created successfully. Access it [here](https://{route_host}).
"""
        apps_git.add_pull_request_comment(pr_id, pr_comment_text, parent_id)

    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)
        shutil.rmtree(root_tmp_dir, ignore_errors=True)

    if create_pr and branch != "master":
        title = "Updated preview environemnt for " + gitops_config.application_name
        description = f"""
This Pull Request is automatically created through [gitopscli](https://github.com/baloise-incubator/gitopscli).
"""
        pull_request = root_git.create_pull_request(branch, "master", title, description)
        print(f"Pull request created: {root_git.get_pull_request_url(pull_request)}")

        if auto_merge:
            root_git.merge_pull_request(pull_request)
            print("Pull request merged")

            root_git.delete_branch(branch)
            print(f"Branch '{branch}' deleted")

import os
import shutil
import uuid
import hashlib

from gitopscli.git.create_git import create_git
from gitopscli.yaml.yaml_util import yaml_load, update_yaml_file

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
        gitops_config_file = apps_git.get_full_file_path(".gitops.config.yaml")
        with open(gitops_config_file, "r") as stream:
            gitops_config_content = yaml_load(stream)
        root_organisation = gitops_config_content["team-config-org"]
        root_repository_name = gitops_config_content["team-config-repo"]
        app_name = gitops_config_content["application-name"]

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
        root_git.checkout("master")
        root_git.new_branch(branch)
        new_preview_folder_name = app_name + "-" + shortened_branch_hash + "-preview"
        preview_template_folder_name = ".preview-templates/" + app_name
        route_host = None
        if not os.path.exists(root_git.get_full_file_path(new_preview_folder_name)):
            shutil.copytree(
                root_git.get_full_file_path(preview_template_folder_name),
                root_git.get_full_file_path(new_preview_folder_name),
            )
            chart_file_path = new_preview_folder_name + "/Chart.yaml"
            if root_git.get_full_file_path(chart_file_path):
                update_yaml_file(root_git.get_full_file_path(chart_file_path), "name", new_preview_folder_name)
                if "routepaths" in gitops_config_content and gitops_config_content["routepaths"] is not None:
                    route_host = gitops_config_content["routehost"].replace("previewplaceholder", shortened_branch_hash)
                    for route_path in gitops_config_content["routepaths"]:
                        yaml_replace_path = route_path["hostpath"]
                        update_yaml_file(
                            root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"),
                            yaml_replace_path,
                            route_host,
                        )

            root_git.commit(f"Initiated new preview env for branch {branch}'")

        new_image_tag = apps_git.get_last_commit_hash()
        if "imagepaths" in gitops_config_content and gitops_config_content["imagepaths"] is not None:
            for route_path in gitops_config_content["imagepaths"]:
                yaml_replace_path = route_path["yamlpath"]
                update_yaml_file(
                    root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"),
                    yaml_replace_path,
                    new_image_tag,
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
        title = "Updated preview environemnt for " + app_name
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

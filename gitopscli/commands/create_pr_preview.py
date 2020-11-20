from gitopscli.commands.create_preview import create_preview_command
from gitopscli.git import GitApiConfig, GitRepoApiFactory


def create_pr_preview_command(
    command,
    pr_id,
    parent_id,
    username,
    password,
    git_user,
    git_email,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "create-pr-preview"
    git_api_config = GitApiConfig(username, password, git_provider, git_provider_url,)
    git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name)

    pr_branch = git_repo_api.get_pull_request_branch(pr_id)
    git_hash = git_repo_api.get_branch_head_hash(pr_branch)

    add_pr_comment = lambda comment: git_repo_api.add_pull_request_comment(pr_id, comment, parent_id)

    create_preview_command(
        command="create-preview",
        username=username,
        password=password,
        git_user=git_user,
        git_email=git_email,
        organisation=organisation,
        repository_name=repository_name,
        git_provider=git_provider,
        git_provider_url=git_provider_url,
        git_hash=git_hash,
        preview_id=pr_branch,  # use pr_branch as preview id
        deployment_already_up_to_date_callback=lambda route_host: add_pr_comment(
            f"The version `{git_hash}` has already been deployed. Access it here: https://{route_host}",
        ),
        deployment_exists_callback=lambda route_host: add_pr_comment(
            f"Preview environment updated to version `{git_hash}`. Access it here: https://{route_host}"
        ),
        deployment_new_callback=lambda route_host: add_pr_comment(
            f"New preview environment created for version `{git_hash}`. Access it here: https://{route_host}"
        ),
    )

from typing import Optional
from gitopscli.commands import delete_preview_command


def delete_pr_preview_command(
    command: str,
    branch: str,
    username: Optional[str],
    password: Optional[str],
    git_user: str,
    git_email: str,
    organisation: str,
    repository_name: str,
    git_provider: Optional[str],
    git_provider_url: Optional[str],
    expect_preview_exists: bool,
) -> None:
    assert command == "delete-pr-preview"
    delete_preview_command(
        command="delete-preview",
        username=username,
        password=password,
        git_user=git_user,
        git_email=git_email,
        organisation=organisation,
        repository_name=repository_name,
        git_provider=git_provider,
        git_provider_url=git_provider_url,
        preview_id=branch,  # use branch as preview id
        expect_preview_exists=expect_preview_exists,
    )

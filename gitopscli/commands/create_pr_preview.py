from dataclasses import dataclass
from typing import Callable, Optional
from gitopscli.git_api import GitApiConfig, GitRepoApiFactory
from .create_preview import CreatePreviewCommand
from .command import Command


class CreatePrPreviewCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        git_user: str
        git_email: str

        git_co_author_name: Optional[str]
        git_co_author_email: Optional[str]

        organisation: str
        repository_name: str

        pr_id: int
        parent_id: Optional[int]

    def __init__(self, args: Args) -> None:
        self.__args = args

    def execute(self) -> None:
        args = self.__args
        git_repo_api = GitRepoApiFactory.create(args, args.organisation, args.repository_name)

        pr_branch = git_repo_api.get_pull_request_branch(args.pr_id)
        git_hash = git_repo_api.get_branch_head_hash(pr_branch)

        add_pr_comment: Callable[[str], None] = lambda comment: git_repo_api.add_pull_request_comment(
            args.pr_id, comment, args.parent_id
        )

        create_preview_command = CreatePreviewCommand(
            CreatePreviewCommand.Args(
                username=args.username,
                password=args.password,
                git_user=args.git_user,
                git_email=args.git_email,
                git_co_author_name=args.git_co_author_name,
                git_co_author_email=args.git_co_author_email,
                organisation=args.organisation,
                repository_name=args.repository_name,
                git_provider=args.git_provider,
                git_provider_url=args.git_provider_url,
                git_hash=git_hash,
                preview_id=pr_branch,  # use pr_branch as preview id
            ),
        )
        create_preview_command.register_callbacks(
            deployment_already_up_to_date_callback=add_pr_comment,
            deployment_updated_callback=add_pr_comment,
            deployment_created_callback=add_pr_comment,
        )
        create_preview_command.execute()

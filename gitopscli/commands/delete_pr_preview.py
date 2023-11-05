from dataclasses import dataclass

from gitopscli.git_api import GitApiConfig

from .command import Command
from .delete_preview import DeletePreviewCommand


class DeletePrPreviewCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        git_user: str
        git_email: str

        git_author_name: str | None
        git_author_email: str | None

        organisation: str
        repository_name: str

        branch: str
        expect_preview_exists: bool

    def __init__(self, args: Args) -> None:
        self.__args = args

    def execute(self) -> None:
        args = self.__args
        DeletePreviewCommand(
            DeletePreviewCommand.Args(
                username=args.username,
                password=args.password,
                git_user=args.git_user,
                git_email=args.git_email,
                git_author_name=args.git_author_name,
                git_author_email=args.git_author_email,
                organisation=args.organisation,
                repository_name=args.repository_name,
                git_provider=args.git_provider,
                git_provider_url=args.git_provider_url,
                preview_id=args.branch,  # use branch as preview id
                expect_preview_exists=args.expect_preview_exists,
            ),
        ).execute()

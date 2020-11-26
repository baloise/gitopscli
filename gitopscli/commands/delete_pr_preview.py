from typing import Optional, NamedTuple
from .delete_preview import DeletePreviewCommand
from .command import Command


class DeletePrPreviewCommand(Command):
    class Args(NamedTuple):
        git_provider: Optional[str]
        git_provider_url: Optional[str]

        username: str
        password: str

        git_user: str
        git_email: str

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
                organisation=args.organisation,
                repository_name=args.repository_name,
                git_provider=args.git_provider,
                git_provider_url=args.git_provider_url,
                preview_id=args.branch,  # use branch as preview id
                expect_preview_exists=args.expect_preview_exists,
            )
        ).execute()

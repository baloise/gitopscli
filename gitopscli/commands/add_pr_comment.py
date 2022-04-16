from dataclasses import dataclass
from typing import Optional
from gitopscli.git_api import GitApiConfig, GitRepoApiFactory
from .command import Command


class AddPrCommentCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        organisation: str
        repository_name: str

        pr_id: int
        parent_id: Optional[int]
        text: str

    def __init__(self, args: Args) -> None:
        self.__args = args

    def execute(self) -> None:
        args = self.__args
        git_repo_api = GitRepoApiFactory.create(args, args.organisation, args.repository_name)
        git_repo_api.add_pull_request_comment(args.pr_id, args.text, args.parent_id)

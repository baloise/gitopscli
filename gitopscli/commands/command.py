from abc import ABCMeta, abstractmethod
from typing import Callable, Union
from .add_pr_comment import pr_comment_command, AddPrCommentArgs
from .create_preview import create_preview_command, CreatePreviewArgs
from .create_pr_preview import create_pr_preview_command, CreatePrPreviewArgs
from .delete_preview import delete_preview_command, DeletePreviewArgs
from .delete_pr_preview import delete_pr_preview_command, DeletePrPreviewArgs
from .deploy import deploy_command, DeployArgs
from .sync_apps import sync_apps_command, SyncAppsArgs
from .version import version_command, VersionArgs

CommandArgs = Union[
    DeployArgs,
    SyncAppsArgs,
    AddPrCommentArgs,
    CreatePreviewArgs,
    CreatePrPreviewArgs,
    DeletePreviewArgs,
    DeletePrPreviewArgs,
    VersionArgs,
]


class Command(metaclass=ABCMeta):
    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError


class _CommandFuncWrapper(Command):
    def __init__(self, command_func: Callable[[], None]) -> None:
        self.__command_func = command_func

    def execute(self) -> None:
        self.__command_func()


class CommandFactory:
    @staticmethod
    def create(args: CommandArgs) -> Command:
        if isinstance(args, DeployArgs):
            deploy_args = args
            func = lambda: deploy_command(deploy_args)
        elif isinstance(args, SyncAppsArgs):
            sync_app_args = args
            func = lambda: sync_apps_command(sync_app_args)
        elif isinstance(args, AddPrCommentArgs):
            add_pr_comment_args = args
            func = lambda: pr_comment_command(add_pr_comment_args)
        elif isinstance(args, CreatePreviewArgs):
            create_preview_args = args
            func = lambda: create_preview_command(create_preview_args)
        elif isinstance(args, CreatePrPreviewArgs):
            create_pr_preview_args = args
            func = lambda: create_pr_preview_command(create_pr_preview_args)
        elif isinstance(args, DeletePreviewArgs):
            delete_preview_args = args
            func = lambda: delete_preview_command(delete_preview_args)
        elif isinstance(args, DeletePrPreviewArgs):
            delete_pr_preview_args = args
            func = lambda: delete_pr_preview_command(delete_pr_preview_args)
        elif isinstance(args, VersionArgs):
            func = version_command
        else:
            raise NotImplementedError(f"Command for {type(args)} not implemented!")
        return _CommandFuncWrapper(func)

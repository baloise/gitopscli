from typing import Union
from .command import Command
from .add_pr_comment import AddPrCommentCommand
from .create_preview import CreatePreviewCommand
from .create_pr_preview import CreatePrPreviewCommand
from .delete_preview import DeletePreviewCommand
from .delete_pr_preview import DeletePrPreviewCommand
from .deploy import DeployCommand
from .sync_apps import SyncAppsCommand
from .version import VersionCommand

CommandArgs = Union[
    DeployCommand.Args,
    DeployCommand.Args,
    AddPrCommentCommand.Args,
    CreatePreviewCommand.Args,
    CreatePrPreviewCommand.Args,
    DeletePreviewCommand.Args,
    DeletePrPreviewCommand.Args,
    SyncAppsCommand.Args,
    VersionCommand.Args,
]


class CommandFactory:
    @staticmethod
    def create(args: CommandArgs) -> Command:
        command: Command
        if isinstance(args, DeployCommand.Args):
            command = DeployCommand(args)
        elif isinstance(args, SyncAppsCommand.Args):
            command = SyncAppsCommand(args)
        elif isinstance(args, AddPrCommentCommand.Args):
            command = AddPrCommentCommand(args)
        elif isinstance(args, CreatePreviewCommand.Args):
            command = CreatePreviewCommand(args)
        elif isinstance(args, CreatePrPreviewCommand.Args):
            command = CreatePrPreviewCommand(args)
        elif isinstance(args, DeletePreviewCommand.Args):
            command = DeletePreviewCommand(args)
        elif isinstance(args, DeletePrPreviewCommand.Args):
            command = DeletePrPreviewCommand(args)
        elif isinstance(args, VersionCommand.Args):
            command = VersionCommand(args)
        else:
            raise NotImplementedError(f"Command for {type(args)} not implemented!")
        return command

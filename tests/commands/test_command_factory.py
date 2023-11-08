import unittest
from unittest.mock import Mock

from gitopscli.commands.add_pr_comment import AddPrCommentCommand
from gitopscli.commands.command_factory import CommandFactory
from gitopscli.commands.create_pr_preview import CreatePrPreviewCommand
from gitopscli.commands.create_preview import CreatePreviewCommand
from gitopscli.commands.delete_pr_preview import DeletePrPreviewCommand
from gitopscli.commands.delete_preview import DeletePreviewCommand
from gitopscli.commands.deploy import DeployCommand
from gitopscli.commands.sync_apps import SyncAppsCommand
from gitopscli.commands.version import VersionCommand


class CommandFactoryTest(unittest.TestCase):
    def test_create_deploy_command(self):
        args = Mock(spec=DeployCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(DeployCommand, type(command))

    def test_create_sync_apps_command(self):
        args = Mock(spec=SyncAppsCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(SyncAppsCommand, type(command))

    def test_create_create_preview_command(self):
        args = Mock(spec=CreatePreviewCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(CreatePreviewCommand, type(command))

    def test_create_create_pr_preview_command(self):
        args = Mock(spec=CreatePrPreviewCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(CreatePrPreviewCommand, type(command))

    def test_create_delete_preview_command(self):
        args = Mock(spec=DeletePreviewCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(DeletePreviewCommand, type(command))

    def test_create_delete_pr_preview_command(self):
        args = Mock(spec=DeletePrPreviewCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(DeletePrPreviewCommand, type(command))

    def test_create_add_pr_comment_command(self):
        args = Mock(spec=AddPrCommentCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(AddPrCommentCommand, type(command))

    def test_create_version_command(self):
        args = Mock(spec=VersionCommand.Args)
        command = CommandFactory.create(args)
        self.assertEqual(VersionCommand, type(command))

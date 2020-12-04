import unittest
from gitopscli.git import GitProvider
from gitopscli.commands.delete_pr_preview import DeletePrPreviewCommand, DeletePreviewCommand
from .mock_mixin import MockMixin


class DeletePrPreviewCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(DeletePrPreviewCommand)

        self.delete_preview_command_mock = self.monkey_patch(DeletePreviewCommand)
        self.delete_preview_command_mock.Args = DeletePreviewCommand.Args
        self.delete_preview_command_mock.return_value = self.delete_preview_command_mock
        self.delete_preview_command_mock.execute.return_value = None

        self.seal_mocks()

    def test_delete_pr_preview(self):
        DeletePrPreviewCommand(
            DeletePrPreviewCommand.Args(
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORGA",
                repository_name="REPO",
                git_provider=GitProvider.GITHUB,
                git_provider_url="URL",
                branch="some/branch",
                expect_preview_exists=True,
            )
        ).execute()

        self.delete_preview_command_mock.assert_called_once_with(
            DeletePreviewCommand.Args(
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORGA",
                repository_name="REPO",
                git_provider=GitProvider.GITHUB,
                git_provider_url="URL",
                preview_id="some/branch",  # call DeletePreviewCommand with branch as preview_id
                expect_preview_exists=True,
            )
        )
        self.delete_preview_command_mock.execute.assert_called_once()

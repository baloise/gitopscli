import unittest
from unittest.mock import patch
from gitopscli.git import GitProvider
from gitopscli.commands.delete_pr_preview import DeletePrPreviewCommand, DeletePreviewCommand


class DeletePrPreviewCommandTest(unittest.TestCase):
    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Inject DeletePreviewCommand mock:
        self.delete_preview_command_mock = add_patch("gitopscli.commands.delete_pr_preview.DeletePreviewCommand")
        self.delete_preview_command_mock.Args = DeletePreviewCommand.Args
        self.delete_preview_command_mock.return_value = self.delete_preview_command_mock

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

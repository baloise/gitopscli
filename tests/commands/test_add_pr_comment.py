import unittest
from uuid import UUID
from unittest.mock import patch, MagicMock, Mock, call
import pytest
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.add_pr_comment import pr_comment_command


class AddPrCommentCommandTest(unittest.TestCase):
    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.logging_mock = add_patch("gitopscli.commands.add_pr_comment.logging")
        self.create_git_mock = add_patch("gitopscli.commands.add_pr_comment.create_git")
        self.git_util_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.create_git_mock, "create_git")
        self.mock_manager.attach_mock(self.git_util_mock, "git_util")
        self.mock_manager.attach_mock(self.logging_mock, "logging")

        # Define some common default return values
        self.create_git_mock.return_value = self.git_util_mock

    def test_with_parent_id(self):
        pr_comment_command(
            command="add-pr-comment",
            text="Hello World!",
            username="USERNAME",
            password="PASSWORD",
            parent_id="<PARENT ID>",
            pr_id="<PR ID>",
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.mock_calls == [
            call.create_git("USERNAME", "PASSWORD", None, None, "ORGA", "REPO", "github", None, None),
            call.logging.info(
                "Creating comment for PR %s as reply to comment %s with content: %s",
                "<PR ID>",
                "<PARENT ID>",
                "Hello World!",
            ),
            call.git_util.add_pull_request_comment("<PR ID>", "Hello World!", "<PARENT ID>"),
        ]

    def test_without_parent_id(self):
        pr_comment_command(
            command="add-pr-comment",
            text="Hello World!",
            username="USERNAME",
            password="PASSWORD",
            parent_id=None,
            pr_id="<PR ID>",
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.mock_calls == [
            call.create_git("USERNAME", "PASSWORD", None, None, "ORGA", "REPO", "github", None, None),
            call.logging.info("Creating comment for PR %s with content: %s", "<PR ID>", "Hello World!",),
            call.git_util.add_pull_request_comment("<PR ID>", "Hello World!", None),
        ]

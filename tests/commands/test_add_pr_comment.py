import unittest
from unittest.mock import patch, MagicMock, Mock, call
from gitopscli.commands.add_pr_comment import pr_comment_command
from gitopscli.git import GitConfig


class PrCommentCommandTest(unittest.TestCase):
    _expected_bitbucket_config = GitConfig(
        username="USERNAME",
        password="PASSWORD",
        git_user="GIT_USER",
        git_email="GIT_EMAIL",
        git_provider="bitbucket-server",
        git_provider_url="bitbucket.tld",
    )

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
        self.git_util_mock.__enter__.return_value = self.git_util_mock
        # self.git_util_mock.add_pull_request_comment.side_effect = lambda x: f"<url of {x}>"

    def test_happy_flow(self):
        pr_comment_command(
            command="add-pr-comment",
            text="some comment text",
            username="USERNAME",
            password="PASSWORD",
            parent_id="parent-0815",
            pr_id="pr-4711",
            organisation="ORGA",
            repository_name="REPO",
            git_provider="bitbucket-server",
            git_provider_url="bitbucket.tld",
        )
        assert self.mock_manager.method_calls == [
            call.create_git(GitConfig(username='USERNAME', password='PASSWORD', git_user=None, git_email=None, git_provider='bitbucket-server', git_provider_url='bitbucket.tld'), 'ORGA', 'REPO'),
            call.logging.info('Creating comment for PR %s as reply to comment %s with content: %s', 'pr-4711', 'parent-0815', 'some comment text'),
            call.git_util.add_pull_request_comment('pr-4711', 'some comment text', 'parent-0815'),
        ]

    def test_happy_flow_no_parent_id(self):
        pr_comment_command(
            command="add-pr-comment",
            text="some comment text",
            username="USERNAME",
            password="PASSWORD",
            pr_id="pr-4711",
            parent_id=None,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="bitbucket-server",
            git_provider_url="bitbucket.tld",
        )
        assert self.mock_manager.method_calls == [
            call.create_git(GitConfig(username='USERNAME', password='PASSWORD', git_user=None, git_email=None, git_provider='bitbucket-server', git_provider_url='bitbucket.tld'), 'ORGA', 'REPO'),
            call.logging.info('Creating comment for PR %s with content: %s', 'pr-4711', 'some comment text'),
            call.git_util.add_pull_request_comment('pr-4711', 'some comment text', None),
        ]

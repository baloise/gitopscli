import unittest
from unittest.mock import patch, MagicMock, Mock, call
from gitopscli.git import GitApiConfig
from gitopscli.commands.add_pr_comment import pr_comment_command


class AddPrCommentCommandTest(unittest.TestCase):
    _expected_github_api_config = GitApiConfig(
        username="USERNAME", password="PASSWORD", git_provider="github", git_provider_url=None,
    )

    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.git_repo_api_factory_mock = add_patch("gitopscli.commands.add_pr_comment.GitRepoApiFactory")
        self.git_repo_api_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.git_repo_api_factory_mock, "GitRepoApiFactory")
        self.mock_manager.attach_mock(self.git_repo_api_mock, "GitRepoApi")

        # Define some common default return values
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock

    def test_with_parent_id(self):
        pr_comment_command(
            command="add-pr-comment",
            text="Hello World!",
            username="USERNAME",
            password="PASSWORD",
            parent_id=4711,
            pr_id=42,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.mock_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepoApi.add_pull_request_comment(42, "Hello World!", 4711),
        ]

    def test_without_parent_id(self):
        pr_comment_command(
            command="add-pr-comment",
            text="Hello World!",
            username="USERNAME",
            password="PASSWORD",
            parent_id=None,
            pr_id=42,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.mock_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepoApi.add_pull_request_comment(42, "Hello World!", None),
        ]

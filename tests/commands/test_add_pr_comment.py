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
        self.logging_mock = add_patch("gitopscli.commands.add_pr_comment.logging")
        self.git_repo_api_factory_mock = add_patch("gitopscli.commands.add_pr_comment.GitRepoApiFactory")
        self.git_repo_api_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.git_repo_api_factory_mock, "GitRepoApiFactory")
        self.mock_manager.attach_mock(self.git_repo_api_mock, "GitRepoApi")
        self.mock_manager.attach_mock(self.logging_mock, "logging")

        # Define some common default return values
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock

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
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.logging.info(
                "Creating comment for PR %s as reply to comment %s with content: %s",
                "<PR ID>",
                "<PARENT ID>",
                "Hello World!",
            ),
            call.GitRepoApi.add_pull_request_comment("<PR ID>", "Hello World!", "<PARENT ID>"),
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
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.logging.info("Creating comment for PR %s with content: %s", "<PR ID>", "Hello World!",),
            call.GitRepoApi.add_pull_request_comment("<PR ID>", "Hello World!", None),
        ]

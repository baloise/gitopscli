import unittest
from unittest.mock import call
from gitopscli.git import GitProvider, GitRepoApi, GitRepoApiFactory
from gitopscli.commands.add_pr_comment import AddPrCommentCommand
from .mock_mixin import MockMixin


class AddPrCommentCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(AddPrCommentCommand)

        git_repo_api_mock = self.create_mock(GitRepoApi)
        git_repo_api_mock.add_pull_request_comment.return_value = None

        git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)
        git_repo_api_factory_mock.create.return_value = git_repo_api_mock

        self.seal_mocks()

    def test_with_parent_id(self):
        args = AddPrCommentCommand.Args(
            text="Hello World!",
            username="USERNAME",
            password="PASSWORD",
            parent_id=4711,
            pr_id=42,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
        )
        AddPrCommentCommand(args).execute()

        assert self.mock_manager.mock_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepoApi.add_pull_request_comment(42, "Hello World!", 4711),
        ]

    def test_without_parent_id(self):
        args = AddPrCommentCommand.Args(
            text="Hello World!",
            username="USERNAME",
            password="PASSWORD",
            parent_id=None,
            pr_id=42,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
        )
        AddPrCommentCommand(args).execute()

        assert self.mock_manager.mock_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepoApi.add_pull_request_comment(42, "Hello World!", None),
        ]

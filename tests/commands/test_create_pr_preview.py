import unittest
from unittest.mock import call

from gitopscli.commands.create_pr_preview import CreatePreviewCommand, CreatePrPreviewCommand
from gitopscli.git_api import GitProvider, GitRepoApi, GitRepoApiFactory

from .mock_mixin import MockMixin

DUMMY_GIT_HASH = "5f65cfa04c66444fcb756d6d7f39304d1c18b199"


class CreatePrPreviewCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(CreatePrPreviewCommand)

        self.create_preview_command_mock = self.monkey_patch(CreatePreviewCommand)
        self.create_preview_command_mock.Args = CreatePreviewCommand.Args
        self.create_preview_command_mock.return_value = self.create_preview_command_mock
        self.create_preview_command_mock.register_callbacks.return_value = None
        self.create_preview_command_mock.execute.return_value = None

        self.git_repo_api_mock = self.create_mock(GitRepoApi)
        self.git_repo_api_mock.get_pull_request_branch.side_effect = lambda pr_id: f"BRANCH_OF_PR_{pr_id}"
        self.git_repo_api_mock.get_branch_head_hash.return_value = DUMMY_GIT_HASH
        self.git_repo_api_mock.add_pull_request_comment.return_value = None

        self.git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock

        self.seal_mocks()

    def test_create_pr_preview(self):
        args = CreatePrPreviewCommand.Args(
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            git_author_name=None,
            git_author_email=None,
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url="URL",
            pr_id=4711,
            parent_id=42,
        )
        CreatePrPreviewCommand(args).execute()

        callbacks = self.create_preview_command_mock.register_callbacks.call_args.kwargs
        deployment_already_up_to_date_callback = callbacks["deployment_already_up_to_date_callback"]
        deployment_updated_callback = callbacks["deployment_updated_callback"]
        deployment_created_callback = callbacks["deployment_created_callback"]

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "ORGA", "REPO"),
            call.GitRepoApi.get_pull_request_branch(4711),
            call.GitRepoApi.get_branch_head_hash("BRANCH_OF_PR_4711"),
            call.CreatePreviewCommand(
                CreatePreviewCommand.Args(
                    username="USERNAME",
                    password="PASSWORD",
                    git_user="GIT_USER",
                    git_email="GIT_EMAIL",
                    git_author_name=None,
                    git_author_email=None,
                    organisation="ORGA",
                    repository_name="REPO",
                    git_provider=GitProvider.GITHUB,
                    git_provider_url="URL",
                    git_hash=DUMMY_GIT_HASH,
                    preview_id="BRANCH_OF_PR_4711",
                )
            ),
            call.CreatePreviewCommand.register_callbacks(
                deployment_already_up_to_date_callback=deployment_already_up_to_date_callback,
                deployment_updated_callback=deployment_updated_callback,
                deployment_created_callback=deployment_created_callback,
            ),
            call.CreatePreviewCommand.execute(),
        ]

        self.mock_manager.reset_mock()
        deployment_already_up_to_date_callback(
            "The version `5f65cfa04c66444fcb756d6d7f39304d1c18b199` has already been deployed. Access it here: https://my-route.baloise.com"
        )
        assert self.mock_manager.method_calls == [
            call.GitRepoApi.add_pull_request_comment(
                4711,
                f"The version `{DUMMY_GIT_HASH}` has already been deployed. "
                "Access it here: https://my-route.baloise.com",
                42,
            )
        ]

        self.mock_manager.reset_mock()
        deployment_updated_callback(
            "Preview environment updated to version `5f65cfa04c66444fcb756d6d7f39304d1c18b199`. Access it here: https://my-route.baloise.com"
        )
        assert self.mock_manager.method_calls == [
            call.GitRepoApi.add_pull_request_comment(
                4711,
                f"Preview environment updated to version `{DUMMY_GIT_HASH}`. "
                "Access it here: https://my-route.baloise.com",
                42,
            )
        ]

        self.mock_manager.reset_mock()
        deployment_created_callback(
            "New preview environment created for version `5f65cfa04c66444fcb756d6d7f39304d1c18b199`. Access it here: https://my-route.baloise.com"
        )
        assert self.mock_manager.method_calls == [
            call.GitRepoApi.add_pull_request_comment(
                4711,
                f"New preview environment created for version `{DUMMY_GIT_HASH}`. "
                "Access it here: https://my-route.baloise.com",
                42,
            )
        ]

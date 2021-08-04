import os
import shutil
import unittest
import logging
from unittest.mock import call, PropertyMock
import pytest
from gitopscli.gitops_config import GitOpsConfig
from gitopscli.git_api import GitRepo, GitRepoApi, GitRepoApiFactory, GitProvider
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.delete_preview import DeletePreviewCommand, load_gitops_config
from .mock_mixin import MockMixin


class DeletePreviewCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(DeletePreviewCommand)

        self.os_mock = self.monkey_patch(os)
        self.os_mock.path.exists.return_value = True

        self.shutil_mock = self.monkey_patch(shutil)
        self.shutil_mock.rmtree.return_value = None

        self.logging_mock = self.monkey_patch(logging)
        self.logging_mock.info.return_value = None

        self.load_gitops_config_mock = self.monkey_patch(load_gitops_config)
        self.load_gitops_config_mock.return_value = GitOpsConfig(
            api_version=0,
            application_name="APP",
            preview_host_template="www.foo.bar",
            preview_template_organisation="PREVIEW_TEMPLATE_ORG",
            preview_template_repository="PREVIEW_TEMPLATE_REPO",
            preview_template_path_template=".preview-templates/my-app",
            preview_template_branch="template-branch",
            preview_target_organisation="PREVIEW_TARGET_ORG",
            preview_target_repository="PREVIEW_TARGET_REPO",
            preview_target_branch="target-branch",
            preview_target_namespace_template="APP-${PREVIEW_ID_HASH}-preview",
            preview_target_max_namespace_length=50,
            replacements={},
        )

        self.git_repo_api_mock = self.create_mock(GitRepoApi)
        self.git_repo_api_mock.create_pull_request.return_value = GitRepoApi.PullRequestIdAndUrl(
            42, "<url of dummy pr>"
        )

        self.git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock

        self.git_repo_mock = self.monkey_patch(GitRepo)
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.__exit__.return_value = False
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.git_repo_mock.clone.return_value = None
        self.git_repo_mock.commit.return_value = None
        self.git_repo_mock.push.return_value = None

        self.seal_mocks()

    def test_delete_existing_happy_flow(self):
        args = DeletePreviewCommand.Args(
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            preview_id="PREVIEW_ID",
            expect_preview_exists=False,
        )
        DeletePreviewCommand(args).execute()
        assert self.mock_manager.method_calls == [
            call.load_gitops_config(args, "ORGA", "REPO"),
            call.GitRepoApiFactory.create(args, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.clone("target-branch"),
            call.logging.info("Preview folder name: %s", "app-685912d3-preview"),
            call.GitRepo.get_full_file_path("app-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/app-685912d3-preview"),
            call.shutil.rmtree("/tmp/created-tmp-dir/app-685912d3-preview", ignore_errors=True),
            call.GitRepo.commit(
                "GIT_USER", "GIT_EMAIL", "Delete preview environment for 'APP' and preview id 'PREVIEW_ID'."
            ),
            call.GitRepo.push(),
        ]

    def test_delete_missing_happy_flow(self):
        self.os_mock.path.exists.return_value = False

        args = DeletePreviewCommand.Args(
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            preview_id="PREVIEW_ID",
            expect_preview_exists=False,
        )
        DeletePreviewCommand(args).execute()
        assert self.mock_manager.method_calls == [
            call.load_gitops_config(args, "ORGA", "REPO"),
            call.GitRepoApiFactory.create(args, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.clone("target-branch"),
            call.logging.info("Preview folder name: %s", "app-685912d3-preview"),
            call.GitRepo.get_full_file_path("app-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/app-685912d3-preview"),
            call.logging.info(
                "No preview environment for '%s' and preview id '%s'. I'm done here.", "APP", "PREVIEW_ID"
            ),
        ]

    def test_delete_missing_but_expected_error(self):
        self.os_mock.path.exists.return_value = False

        args = DeletePreviewCommand.Args(
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            preview_id="PREVIEW_ID",
            expect_preview_exists=True,  # we expect an existing preview
        )
        with pytest.raises(GitOpsException) as ex:
            DeletePreviewCommand(args).execute()
        self.assertEqual(str(ex.value), "There was no preview with name: app-685912d3-preview")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(args, "ORGA", "REPO"),
            call.GitRepoApiFactory.create(args, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.clone("target-branch"),
            call.logging.info("Preview folder name: %s", "app-685912d3-preview"),
            call.GitRepo.get_full_file_path("app-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/app-685912d3-preview"),
        ]

    def test_missing_gitops_config_yaml_error(self):
        self.load_gitops_config_mock.side_effect = GitOpsException()

        args = DeletePreviewCommand.Args(
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORGA",
            repository_name="REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
            preview_id="PREVIEW_ID",
            expect_preview_exists=True,  # we expect an existing preview
        )
        with pytest.raises(GitOpsException):
            DeletePreviewCommand(args).execute()
        assert self.mock_manager.method_calls == [
            call.load_gitops_config(args, "ORGA", "REPO"),
        ]

import unittest
from uuid import UUID
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, Mock, call
import pytest
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.delete_preview import delete_preview_command


class DeletePreviewCommandTest(unittest.TestCase):
    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.os_path_exists_mock = add_patch("gitopscli.commands.delete_preview.os.path.exists")
        self.shutil_rmtree_mock = add_patch("gitopscli.commands.delete_preview.shutil.rmtree")
        self.create_tmp_dir_mock = add_patch("gitopscli.commands.delete_preview.create_tmp_dir")
        self.delete_tmp_dir_mock = add_patch("gitopscli.commands.delete_preview.delete_tmp_dir")
        self.logging_mock = add_patch("gitopscli.commands.delete_preview.logging")
        self.create_git_mock = add_patch("gitopscli.commands.delete_preview.create_git")
        self.git_util_mock = MagicMock()
        self.gitops_config_mock = add_patch("gitopscli.commands.delete_preview.GitOpsConfig")
        self.gitops_config_team_config_org_mock = add_patch(
            "gitopscli.commands.delete_preview.GitOpsConfig.team_config_org"
        )

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.create_tmp_dir_mock, "create_tmp_dir")
        self.mock_manager.attach_mock(self.create_git_mock, "create_git")
        self.mock_manager.attach_mock(self.git_util_mock, "git_util")
        self.mock_manager.attach_mock(self.delete_tmp_dir_mock, "delete_tmp_dir")
        self.mock_manager.attach_mock(self.os_path_exists_mock, "os.path.exists")
        self.mock_manager.attach_mock(self.shutil_rmtree_mock, "shutil.rmtree")
        self.mock_manager.attach_mock(self.logging_mock, "logging")
        self.mock_manager.attach_mock(self.gitops_config_mock, "GitOpsConfig")
        self.mock_manager.attach_mock(self.gitops_config_team_config_org_mock, "GitOpsConfig.team_config_org")

        # Define some common default return values
        self.create_tmp_dir_side_effect_count = 0

        def create_tmp_dir_side_effect():
            self.create_tmp_dir_side_effect_count += 1
            return f"/tmp/created-tmp-dir-{self.create_tmp_dir_side_effect_count}"

        self.create_tmp_dir_mock.side_effect = create_tmp_dir_side_effect

        self.create_git_mock.return_value = self.git_util_mock
        self.git_util_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.git_util_mock.create_pull_request.return_value = "<dummy-pr-object>"
        self.git_util_mock.get_pull_request_url.side_effect = lambda x: f"<url of {x}>"
        self.os_path_exists_mock.return_value = True
        self.gitops_config_mock.return_value = SimpleNamespace(
            team_config_org="TEAM_CONFIG_ORG", team_config_repo="TEAM_CONFIG_REPO", application_name="APP"
        )

    def test_delete_existing_happy_flow(self):
        delete_preview_command(
            command="delete-preview",
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
            preview_id="PREVIEW_ID",
            expect_preview_exists=False,
        )

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME",
                "PASSWORD",
                "GIT_USER",
                "GIT_EMAIL",
                "ORGA",
                "REPO",
                "github",
                None,
                "/tmp/created-tmp-dir-1",
            ),
            call.git_util.checkout("master"),
            call.logging.info("App repo '%s/%s' branch 'master' checkout successful", "ORGA", "REPO"),
            call.git_util.get_full_file_path(".gitops.config.yaml"),
            call.GitOpsConfig("/tmp/created-tmp-dir/.gitops.config.yaml"),
            call.logging.info("Read .gitops.config.yaml"),
            call.create_git(
                "USERNAME",
                "PASSWORD",
                "GIT_USER",
                "GIT_EMAIL",
                "TEAM_CONFIG_ORG",
                "TEAM_CONFIG_REPO",
                "github",
                None,
                "/tmp/created-tmp-dir-2",
            ),
            call.git_util.checkout("master"),
            call.logging.info(
                "Config repo '%s/%s' branch 'master' checkout successful", "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO"
            ),
            call.logging.info("Preview folder name: %s", "APP-685912d3-preview"),
            call.git_util.get_full_file_path("APP-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/APP-685912d3-preview"),
            call.shutil.rmtree("/tmp/created-tmp-dir/APP-685912d3-preview", ignore_errors=True),
            call.git_util.commit("Delete preview environment for 'APP' and preview id 'PREVIEW_ID'."),
            call.git_util.push("master"),
            call.logging.info("Pushed branch 'master'"),
            call.delete_tmp_dir("/tmp/created-tmp-dir-1"),
            call.delete_tmp_dir("/tmp/created-tmp-dir-2"),
        ]

    def test_delete_missing_happy_flow(self):
        self.os_path_exists_mock.return_value = False

        delete_preview_command(
            command="delete-preview",
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
            preview_id="PREVIEW_ID",
            expect_preview_exists=False,
        )

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME",
                "PASSWORD",
                "GIT_USER",
                "GIT_EMAIL",
                "ORGA",
                "REPO",
                "github",
                None,
                "/tmp/created-tmp-dir-1",
            ),
            call.git_util.checkout("master"),
            call.logging.info("App repo '%s/%s' branch 'master' checkout successful", "ORGA", "REPO"),
            call.git_util.get_full_file_path(".gitops.config.yaml"),
            call.GitOpsConfig("/tmp/created-tmp-dir/.gitops.config.yaml"),
            call.logging.info("Read .gitops.config.yaml"),
            call.create_git(
                "USERNAME",
                "PASSWORD",
                "GIT_USER",
                "GIT_EMAIL",
                "TEAM_CONFIG_ORG",
                "TEAM_CONFIG_REPO",
                "github",
                None,
                "/tmp/created-tmp-dir-2",
            ),
            call.git_util.checkout("master"),
            call.logging.info(
                "Config repo '%s/%s' branch 'master' checkout successful", "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO"
            ),
            call.logging.info("Preview folder name: %s", "APP-685912d3-preview"),
            call.git_util.get_full_file_path("APP-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/APP-685912d3-preview"),
            call.logging.info(
                "No preview environment for '%s' and preview id '%s'. Nothing to do..", "APP", "PREVIEW_ID"
            ),
            call.delete_tmp_dir("/tmp/created-tmp-dir-1"),
            call.delete_tmp_dir("/tmp/created-tmp-dir-2"),
        ]

    def test_delete_missing_but_expected_error(self):
        self.os_path_exists_mock.return_value = False
        self.git_util_mock.checkout.side_effect

        FileNotFoundError

        with pytest.raises(GitOpsException) as ex:
            delete_preview_command(
                command="delete-preview",
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORGA",
                repository_name="REPO",
                git_provider="github",
                git_provider_url=None,
                preview_id="PREVIEW_ID",
                expect_preview_exists=True,  # we expect an existing preview
            )
        self.assertEqual(str(ex.value), "There was no preview with name: APP-685912d3-preview")

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME",
                "PASSWORD",
                "GIT_USER",
                "GIT_EMAIL",
                "ORGA",
                "REPO",
                "github",
                None,
                "/tmp/created-tmp-dir-1",
            ),
            call.git_util.checkout("master"),
            call.logging.info("App repo '%s/%s' branch 'master' checkout successful", "ORGA", "REPO"),
            call.git_util.get_full_file_path(".gitops.config.yaml"),
            call.GitOpsConfig("/tmp/created-tmp-dir/.gitops.config.yaml"),
            call.logging.info("Read .gitops.config.yaml"),
            call.create_git(
                "USERNAME",
                "PASSWORD",
                "GIT_USER",
                "GIT_EMAIL",
                "TEAM_CONFIG_ORG",
                "TEAM_CONFIG_REPO",
                "github",
                None,
                "/tmp/created-tmp-dir-2",
            ),
            call.git_util.checkout("master"),
            call.logging.info(
                "Config repo '%s/%s' branch 'master' checkout successful", "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO"
            ),
            call.logging.info("Preview folder name: %s", "APP-685912d3-preview"),
            call.git_util.get_full_file_path("APP-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/APP-685912d3-preview"),
            call.delete_tmp_dir("/tmp/created-tmp-dir-1"),
            call.delete_tmp_dir("/tmp/created-tmp-dir-2"),
        ]

    def test_missing_gitops_config_yaml_error(self):
        self.gitops_config_mock.side_effect = FileNotFoundError()

        with pytest.raises(GitOpsException) as ex:
            delete_preview_command(
                command="delete-preview",
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORGA",
                repository_name="REPO",
                git_provider="github",
                git_provider_url=None,
                preview_id="PREVIEW_ID",
                expect_preview_exists=True,  # we expect an existing preview
            )
        self.assertEqual(str(ex.value), "Couldn't find .gitops.config.yaml")

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME",
                "PASSWORD",
                "GIT_USER",
                "GIT_EMAIL",
                "ORGA",
                "REPO",
                "github",
                None,
                "/tmp/created-tmp-dir-1",
            ),
            call.git_util.checkout("master"),
            call.logging.info("App repo '%s/%s' branch 'master' checkout successful", "ORGA", "REPO"),
            call.git_util.get_full_file_path(".gitops.config.yaml"),
            call.GitOpsConfig("/tmp/created-tmp-dir/.gitops.config.yaml"),
            call.delete_tmp_dir("/tmp/created-tmp-dir-1"),
            call.delete_tmp_dir("/tmp/created-tmp-dir-2"),
        ]

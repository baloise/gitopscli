import unittest
from uuid import UUID
from unittest.mock import patch, MagicMock, Mock, call
import pytest
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.deploy import deploy_command
from gitopscli.git import GitApiConfig, GitRepoApi


class DeployCommandTest(unittest.TestCase):
    _expected_github_api_config = GitApiConfig(
        username="USERNAME", password="PASSWORD", git_provider="github", git_provider_url=None,
    )

    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.os_path_isfile_mock = add_patch("gitopscli.commands.deploy.os.path.isfile")
        self.update_yaml_file_mock = add_patch("gitopscli.commands.deploy.update_yaml_file")
        self.logging_mock = add_patch("gitopscli.commands.deploy.logging")
        self.uuid_mock = add_patch("gitopscli.commands.deploy.uuid")
        self.git_repo_api_factory_mock = add_patch("gitopscli.commands.deploy.GitRepoApiFactory")
        self.git_repo_mock = add_patch("gitopscli.commands.deploy.GitRepo")

        self.git_repo_api_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.git_repo_api_factory_mock, "GitRepoApiFactory")
        self.mock_manager.attach_mock(self.git_repo_api_mock, "GitRepoApi")
        self.mock_manager.attach_mock(self.git_repo_mock, "GitRepo")
        self.mock_manager.attach_mock(self.update_yaml_file_mock, "update_yaml_file")
        self.mock_manager.attach_mock(self.os_path_isfile_mock, "os.path.isfile")
        self.mock_manager.attach_mock(self.logging_mock, "logging")

        # Define some common default return values
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock
        self.git_repo_api_mock.create_pull_request.return_value = GitRepoApi.PullRequestIdAndUrl(
            "<dummy pr id>", "<url of dummy pr>"
        )
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.os_path_isfile_mock.return_value = True
        self.update_yaml_file_mock.return_value = True
        self.uuid_mock.uuid4.return_value = UUID("b973b5bb-64a6-4735-a840-3113d531b41c")

    def test_happy_flow(self):
        deploy_command(
            command="deploy",
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.d' to 'bar' in test/file.yml"),
            call.GitRepo.push("master"),
        ]

    def test_create_pr_happy_flow(self):
        deploy_command(
            command="deploy",
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=True,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.new_branch("gitopscli-deploy-b973b5bb"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.d' to 'bar' in test/file.yml"),
            call.GitRepo.push("gitopscli-deploy-b973b5bb"),
            call.GitRepoApi.create_pull_request(
                "gitopscli-deploy-b973b5bb",
                "master",
                "Updated values in test/file.yml",
                "Updated 2 values in `test/file.yml`:\n```yaml\na.b.c: foo\na.b.d: bar\n```\n",
            ),
        ]

    def test_create_pr_and_merge_happy_flow(self):
        deploy_command(
            command="deploy",
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=True,
            auto_merge=True,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.new_branch("gitopscli-deploy-b973b5bb"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "changed 'a.b.d' to 'bar' in test/file.yml"),
            call.GitRepo.push("gitopscli-deploy-b973b5bb"),
            call.GitRepoApi.create_pull_request(
                "gitopscli-deploy-b973b5bb",
                "master",
                "Updated values in test/file.yml",
                "Updated 2 values in `test/file.yml`:\n```yaml\na.b.c: foo\na.b.d: bar\n```\n",
            ),
            call.GitRepoApi.merge_pull_request("<dummy pr id>"),
            call.GitRepoApi.delete_branch("gitopscli-deploy-b973b5bb"),
        ]

    def test_single_commit_happy_flow(self):
        deploy_command(
            command="deploy",
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=True,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "updated 2 values in test/file.yml\n\na.b.c: foo\na.b.d: bar"),
            call.GitRepo.push("master"),
        ]

    def test_commit_message_happy_flow(self):
        deploy_command(
            command="deploy",
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
            commit_message="testcommit",
        )

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.GitRepo.commit("GIT_USER", "GIT_EMAIL", "testcommit"),
            call.GitRepo.push("master"),
        ]

    def test_checkout_error(self):
        checkout_exception = GitOpsException("dummy checkout error")
        self.git_repo_mock.checkout.side_effect = checkout_exception

        with pytest.raises(GitOpsException) as ex:
            deploy_command(
                command="deploy",
                file="test/file.yml",
                values={"a.b.c": "foo", "a.b.d": "bar"},
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                create_pr=False,
                auto_merge=False,
                single_commit=False,
                organisation="ORGA",
                repository_name="REPO",
                git_provider="github",
                git_provider_url=None,
            )
        self.assertEqual(ex.value, checkout_exception)

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
        ]

    def test_file_not_found(self):
        self.os_path_isfile_mock.return_value = False

        with pytest.raises(GitOpsException) as ex:
            deploy_command(
                command="deploy",
                file="test/file.yml",
                values={"a.b.c": "foo", "a.b.d": "bar"},
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                create_pr=False,
                auto_merge=False,
                single_commit=False,
                organisation="ORGA",
                repository_name="REPO",
                git_provider="github",
                git_provider_url=None,
            )
        self.assertEqual(str(ex.value), "No such file: test/file.yml")

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
        ]

    def test_nothing_to_update(self):
        self.update_yaml_file_mock.return_value = False

        deploy_command(
            command="deploy",
            file="test/file.yml",
            values={"a.b.c": "foo", "a.b.d": "bar"},
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            create_pr=False,
            auto_merge=False,
            single_commit=False,
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self._expected_github_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Yaml property %s already up-to-date", "a.b.c"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Yaml property %s already up-to-date", "a.b.d"),
            call.logging.info("All values already up-to-date. I'm done here"),
        ]

import unittest
from uuid import UUID
from unittest.mock import patch, MagicMock, Mock, call
import pytest
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.deploy import deploy_command


class DeployCommandTest(unittest.TestCase):
    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.os_path_isfile_mock = add_patch("gitopscli.commands.deploy.os.path.isfile")
        self.update_yaml_file_mock = add_patch("gitopscli.commands.deploy.update_yaml_file")
        self.create_tmp_dir_mock = add_patch("gitopscli.commands.deploy.create_tmp_dir")
        self.delete_tmp_dir_mock = add_patch("gitopscli.commands.deploy.delete_tmp_dir")
        self.logging_mock = add_patch("gitopscli.commands.deploy.logging")
        self.uuid_mock = add_patch("gitopscli.commands.deploy.uuid")
        self.create_git_mock = add_patch("gitopscli.commands.deploy.create_git")
        self.git_util_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.create_tmp_dir_mock, "create_tmp_dir")
        self.mock_manager.attach_mock(self.create_git_mock, "create_git")
        self.mock_manager.attach_mock(self.git_util_mock, "git_util")
        self.mock_manager.attach_mock(self.delete_tmp_dir_mock, "delete_tmp_dir")
        self.mock_manager.attach_mock(self.update_yaml_file_mock, "update_yaml_file")
        self.mock_manager.attach_mock(self.os_path_isfile_mock, "os.path.isfile")
        self.mock_manager.attach_mock(self.logging_mock, "logging")

        # Define some common default return values
        self.create_git_mock.return_value = self.git_util_mock
        self.create_tmp_dir_mock.return_value = "/tmp/created-tmp-dir"
        self.git_util_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.git_util_mock.create_pull_request.return_value = "<dummy-pr-object>"
        self.git_util_mock.get_pull_request_url.side_effect = lambda x: f"<url of {x}>"
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

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.logging.info("Master checkout successful"),
            call.git_util.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.git_util.commit("changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.git_util.commit("changed 'a.b.d' to 'bar' in test/file.yml"),
            call.git_util.push("master"),
            call.logging.info("Pushed branch %s", "master"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
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

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.logging.info("Master checkout successful"),
            call.git_util.new_branch("gitopscli-deploy-b973b5bb"),
            call.logging.info("Created branch %s", "gitopscli-deploy-b973b5bb"),
            call.git_util.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.git_util.commit("changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.git_util.commit("changed 'a.b.d' to 'bar' in test/file.yml"),
            call.git_util.push("gitopscli-deploy-b973b5bb"),
            call.logging.info("Pushed branch %s", "gitopscli-deploy-b973b5bb"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
            call.git_util.create_pull_request(
                "gitopscli-deploy-b973b5bb",
                "master",
                "Updated values in test/file.yml",
                "Updated 2 values in `test/file.yml`:\n```yaml\na.b.c: foo\na.b.d: bar\n```\n",
            ),
            call.git_util.get_pull_request_url("<dummy-pr-object>"),
            call.logging.info("Pull request created: %s", "<url of <dummy-pr-object>>"),
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

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.logging.info("Master checkout successful"),
            call.git_util.new_branch("gitopscli-deploy-b973b5bb"),
            call.logging.info("Created branch %s", "gitopscli-deploy-b973b5bb"),
            call.git_util.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.git_util.commit("changed 'a.b.c' to 'foo' in test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.git_util.commit("changed 'a.b.d' to 'bar' in test/file.yml"),
            call.git_util.push("gitopscli-deploy-b973b5bb"),
            call.logging.info("Pushed branch %s", "gitopscli-deploy-b973b5bb"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
            call.git_util.create_pull_request(
                "gitopscli-deploy-b973b5bb",
                "master",
                "Updated values in test/file.yml",
                "Updated 2 values in `test/file.yml`:\n```yaml\na.b.c: foo\na.b.d: bar\n```\n",
            ),
            call.git_util.get_pull_request_url("<dummy-pr-object>"),
            call.logging.info("Pull request created: %s", "<url of <dummy-pr-object>>"),
            call.git_util.merge_pull_request("<dummy-pr-object>"),
            call.logging.info("Pull request merged"),
            call.git_util.delete_branch("gitopscli-deploy-b973b5bb"),
            call.logging.info("Branch '%s' deleted", "gitopscli-deploy-b973b5bb"),
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

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.logging.info("Master checkout successful"),
            call.git_util.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.git_util.commit("updated 2 values in test/file.yml\n\na.b.c: foo\na.b.d: bar"),
            call.git_util.push("master"),
            call.logging.info("Pushed branch %s", "master"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
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
            commit_message="testcommit",
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.logging.info("Master checkout successful"),
            call.git_util.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Updated yaml property %s to %s", "a.b.c", "foo"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Updated yaml property %s to %s", "a.b.d", "bar"),
            call.git_util.commit("testcommit"),
            call.git_util.push("master"),
            call.logging.info("Pushed branch %s", "master"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
        ]

    def test_checkout_error(self):
        checkout_exception = GitOpsException("dummy checkout error")
        self.git_util_mock.checkout.side_effect = checkout_exception

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

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
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

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.logging.info("Master checkout successful"),
            call.git_util.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
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

        assert self.mock_manager.mock_calls == [
            call.create_tmp_dir(),
            call.create_git(
                "USERNAME", "PASSWORD", "GIT_USER", "GIT_EMAIL", "ORGA", "REPO", "github", None, "/tmp/created-tmp-dir"
            ),
            call.git_util.checkout("master"),
            call.logging.info("Master checkout successful"),
            call.git_util.get_full_file_path("test/file.yml"),
            call.os.path.isfile("/tmp/created-tmp-dir/test/file.yml"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.c", "foo"),
            call.logging.info("Yaml property %s already up-to-date", "a.b.c"),
            call.update_yaml_file("/tmp/created-tmp-dir/test/file.yml", "a.b.d", "bar"),
            call.logging.info("Yaml property %s already up-to-date", "a.b.d"),
            call.logging.info("All values already up-to-date. I'm done here"),
            call.delete_tmp_dir("/tmp/created-tmp-dir"),
        ]

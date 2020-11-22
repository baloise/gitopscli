from os import path, makedirs, chmod
import stat
import unittest
import uuid
from unittest.mock import MagicMock, patch, call
from git import Repo
import pytest

from gitopscli.git import GitRepo, GitRepoApi
from gitopscli.gitops_exception import GitOpsException


class GitRepoTest(unittest.TestCase):
    def setUp(self):
        self.__origin = self.__create_origin()

        self.__mock_repo_api: GitRepoApi = MagicMock()
        self.__mock_repo_api.get_clone_url.return_value = self.__origin.working_dir
        self.__mock_repo_api.get_username.return_value = None
        self.__mock_repo_api.get_password.return_value = None

    def __create_tmp_dir(self):
        tmp_dir_path = f"/tmp/gitopscli-test-{uuid.uuid4()}"
        makedirs(tmp_dir_path)
        return tmp_dir_path

    def __read_file(self, filename):
        self.assertTrue(filename)
        with open(filename) as input_stream:
            return input_stream.read()

    def __create_origin(self):
        repo_dir = self.__create_tmp_dir()

        repo = Repo.init(repo_dir)
        repo.config_writer().set_value("user", "name", "unit tester").release()
        repo.config_writer().set_value("user", "email", "unit@tester.com").release()

        with open(f"{repo_dir}/README.md", "w") as readme:
            readme.write("master branch readme")
        repo.git.add("--all")
        repo.git.commit("-m", "initial commit")

        repo.create_head("xyz").checkout()

        with open(f"{repo_dir}/README.md", "w") as readme:
            readme.write("xyz branch readme")
        repo.git.add("--all")
        repo.git.commit("-m", "xyz brach commit")

        return repo

    def test_finalize(self):
        testee = GitRepo(self.__mock_repo_api)

        testee.checkout("master")

        tmp_dir = testee.get_full_file_path("..")
        self.assertTrue(path.exists(tmp_dir))

        testee.finalize()
        self.assertFalse(path.exists(tmp_dir))

    def test_enter_and_exit_magic_methods(self):
        testee = GitRepo(self.__mock_repo_api)

        self.assertEqual(testee, testee.__enter__())

        testee.checkout("master")

        tmp_dir = testee.get_full_file_path("..")
        self.assertTrue(path.exists(tmp_dir))

        testee.__exit__(None, None, None)
        self.assertFalse(path.exists(tmp_dir))

    @patch("gitopscli.git.git_repo.logging")
    def test_checkout_without_credentials(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")

            readme = self.__read_file(testee.get_full_file_path("README.md"))
            self.assertEqual("master branch readme", readme)

            self.assertFalse(path.exists(testee.get_full_file_path("../credentials.sh")))
        assert logging_mock.method_calls == [
            call.info("Cloning repository: %s", self.__mock_repo_api.get_clone_url()),
            call.info("Checking out branch: %s", "master"),
        ]

    @patch("gitopscli.git.git_repo.logging")
    def test_checkout_with_credentials(self, logging_mock):
        self.__mock_repo_api.get_username.return_value = "User"
        self.__mock_repo_api.get_password.return_value = "Pass"
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")

            credentials_file = self.__read_file(testee.get_full_file_path("../credentials.sh"))
            self.assertEqual(
                """\
#!/bin/sh
echo username=User
echo password=Pass
""",
                credentials_file,
            )
        assert logging_mock.method_calls == [
            call.info("Cloning repository: %s", self.__mock_repo_api.get_clone_url()),
            call.info("Checking out branch: %s", "master"),
        ]

    @patch("gitopscli.git.git_repo.logging")
    def test_checkout_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("xyz")
            readme = self.__read_file(testee.get_full_file_path("README.md"))
            self.assertEqual("xyz branch readme", readme)
        assert logging_mock.method_calls == [
            call.info("Cloning repository: %s", self.__mock_repo_api.get_clone_url()),
            call.info("Checking out branch: %s", "xyz"),
        ]

    @patch("gitopscli.git.git_repo.logging")
    def test_checkout_unknown_url(self, logging_mock):
        self.__mock_repo_api.get_clone_url.return_value = "invalid_url"
        with GitRepo(self.__mock_repo_api) as testee:
            with pytest.raises(GitOpsException) as ex:
                testee.checkout("master")
            self.assertEqual("Error cloning 'invalid_url'", str(ex.value))
        assert logging_mock.method_calls == [
            call.info("Cloning repository: %s", self.__mock_repo_api.get_clone_url()),
        ]

    @patch("gitopscli.git.git_repo.logging")
    def test_checkout_unknown_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            with pytest.raises(GitOpsException) as ex:
                testee.checkout("foo")
            self.assertEqual("Error checking out branch 'foo'", str(ex.value))
        assert logging_mock.method_calls == [
            call.info("Cloning repository: %s", self.__mock_repo_api.get_clone_url()),
            call.info("Checking out branch: %s", "foo"),
        ]

    def test_get_full_file_path(self):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            self.assertRegex(testee.get_full_file_path("foo.bar"), r"^/tmp/gitopscli/[0-9a-f\-]+/repo/foo\.bar$")

    @patch("gitopscli.git.git_repo.logging")
    def test_new_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            logging_mock.reset_mock()

            testee.new_branch("foo")

            repo = Repo(testee.get_full_file_path("."))
            branches = [str(b) for b in repo.branches]
            self.assertIn("foo", branches)
        logging_mock.info.assert_called_once_with("Creating new branch: %s", "foo")

    @patch("gitopscli.git.git_repo.logging")
    def test_new_branch_name_collision(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            logging_mock.reset_mock()

            with pytest.raises(GitOpsException) as ex:
                testee.new_branch("xyz")
            self.assertEqual("Error creating new branch 'xyz'.", str(ex.value))
        logging_mock.info.assert_called_once_with("Creating new branch: %s", "xyz")

    @patch("gitopscli.git.git_repo.logging")
    def test_commit(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            logging_mock.reset_mock()

            with open(testee.get_full_file_path("foo.md"), "w") as outfile:
                outfile.write("new file")
            with open(testee.get_full_file_path("README.md"), "w") as outfile:
                outfile.write("new content")
            testee.commit(git_user="john doe", git_email="john@doe.com", message="new commit")

            repo = Repo(testee.get_full_file_path("."))
            commits = list(repo.iter_commits("master"))
            self.assertEqual(2, len(commits))
            self.assertEqual("new commit\n", commits[0].message)
            self.assertEqual("john doe", commits[0].author.name)
            self.assertEqual("john@doe.com", commits[0].author.email)
            self.assertIn("foo.md", commits[0].stats.files)
            self.assertIn("README.md", commits[0].stats.files)
        logging_mock.info.assert_called_once_with("Creating commit with message: %s", "new commit")

    @patch("gitopscli.git.git_repo.logging")
    def test_commit_nothing_to_commit(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            logging_mock.reset_mock()

            testee.commit(git_user="john doe", git_email="john@doe.com", message="empty commit")

            repo = Repo(testee.get_full_file_path("."))
            commits = list(repo.iter_commits("master"))
            self.assertEqual(1, len(commits))
            self.assertEqual("initial commit\n", commits[0].message)
        logging_mock.assert_not_called()

    @patch("gitopscli.git.git_repo.logging")
    def test_push(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")

            with open(testee.get_full_file_path("foo.md"), "w") as readme:
                readme.write("new file")
            util_repo = Repo(testee.get_full_file_path("."))
            util_repo.git.add("--all")
            util_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
            util_repo.git.commit("-m", "new commit")

            logging_mock.reset_mock()

            testee.push("master")

            commits = list(self.__origin.iter_commits("master"))
            self.assertEqual(2, len(commits))
            self.assertEqual("new commit\n", commits[0].message)
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "master")

    @patch("gitopscli.git.git_repo.logging")
    def test_push_no_changes(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            logging_mock.reset_mock()

            testee.push("master")
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "master")

    @patch("gitopscli.git.git_repo.logging")
    def test_push_unknown_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            logging_mock.reset_mock()

            with pytest.raises(GitOpsException) as ex:
                testee.push("unknown")
            assert str(ex.value).startswith("Error pushing branch 'unknown' to origin")
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "unknown")

    @patch("gitopscli.git.git_repo.logging")
    def test_push_commit_hook_error_reason_is_shown(self, logging_mock):
        repo_dir = self.__origin.working_dir
        with open(f"{repo_dir}/.git/hooks/pre-receive", "w") as pre_receive_hook:
            pre_receive_hook.write('echo >&2 "we reject this push"; exit 1')
        chmod(f"{repo_dir}/.git/hooks/pre-receive", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")

            with open(testee.get_full_file_path("foo.md"), "w") as readme:
                readme.write("new file")
            util_repo = Repo(testee.get_full_file_path("."))
            util_repo.git.add("--all")
            util_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
            util_repo.git.commit("-m", "new commit")

            logging_mock.reset_mock()

            with pytest.raises(GitOpsException) as ex:
                testee.push("master")
            assert "pre-receive" in str(ex.value) and "we reject this push" in str(ex.value)
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "master")

    def test_get_author_from_last_commit(self):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.checkout("master")
            self.assertEqual("unit tester <unit@tester.com>", testee.get_author_from_last_commit())

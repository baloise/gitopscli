import stat
import unittest
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import Repo

from gitopscli.git_api import GitRepo, GitRepoApi
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
        Path(tmp_dir_path).mkdir(parents=True)
        return tmp_dir_path

    def __read_file(self, filename):
        self.assertTrue(filename)
        with Path(filename).open() as input_stream:
            return input_stream.read()

    def __create_origin(self):
        repo_dir = self.__create_tmp_dir()

        repo = Repo.init(repo_dir, initial_branch="master")
        git_user = "unit tester"
        git_email = "unit@tester.com"
        repo.config_writer().set_value("user", "name", git_user).release()
        repo.config_writer().set_value("user", "email", git_email).release()

        with Path(f"{repo_dir}/README.md").open("w") as readme:
            readme.write("master branch readme")
        repo.git.add("--all")
        repo.git.commit("-m", "initial commit", "--author", f"{git_user} <{git_email}>")

        repo.create_head("xyz").checkout()

        with Path(f"{repo_dir}/README.md").open("w") as readme:
            readme.write("xyz branch readme")
        repo.git.add("--all")
        repo.git.commit("-m", "initial xyz branch commit", "--author", f"{git_user} <{git_email}>")

        repo.git.checkout("master")  # master = default branch
        repo.git.config("receive.denyCurrentBranch", "ignore")

        return repo

    def test_finalize(self):
        testee = GitRepo(self.__mock_repo_api)

        testee.clone()

        tmp_dir = testee.get_full_file_path("..")
        self.assertTrue(Path(tmp_dir).exists())

        testee.finalize()
        self.assertFalse(Path(tmp_dir).exists())

    def test_enter_and_exit_magic_methods(self):
        testee = GitRepo(self.__mock_repo_api)

        self.assertEqual(testee, testee.__enter__())

        testee.clone()

        tmp_dir = testee.get_full_file_path("..")
        self.assertTrue(Path(tmp_dir).exists())

        testee.__exit__(None, None, None)
        self.assertFalse(Path(tmp_dir).exists())

    @patch("gitopscli.git_api.git_repo.logging")
    def test_clone(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            tmp_dir = testee.get_full_file_path("..")
            self.assertTrue(Path(tmp_dir).exists())

            readme = self.__read_file(testee.get_full_file_path("README.md"))
            self.assertEqual("master branch readme", readme)

        self.assertFalse(Path(tmp_dir).exists())
        logging_mock.info.assert_called_once_with("Cloning repository: %s", self.__mock_repo_api.get_clone_url())

    @patch("gitopscli.git_api.git_repo.logging")
    def test_clone_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone("xyz")

            tmp_dir = testee.get_full_file_path("..")
            self.assertTrue(Path(tmp_dir).exists())

            readme = self.__read_file(testee.get_full_file_path("README.md"))
            self.assertEqual("xyz branch readme", readme)

        self.assertFalse(Path(tmp_dir).exists())
        logging_mock.info.assert_called_once_with(
            "Cloning repository: %s (branch: %s)",
            self.__mock_repo_api.get_clone_url(),
            "xyz",
        )

    @patch("gitopscli.git_api.git_repo.logging")
    def test_clone_unknown_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            with pytest.raises(GitOpsException) as ex:
                testee.clone("unknown")
            self.assertEqual(
                f"Error cloning branch 'unknown' of '{self.__mock_repo_api.get_clone_url()}'",
                str(ex.value),
            )

        logging_mock.info.assert_called_once_with(
            "Cloning repository: %s (branch: %s)",
            self.__mock_repo_api.get_clone_url(),
            "unknown",
        )

    @patch("gitopscli.git_api.git_repo.logging")
    def test_clone_without_credentials(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            readme = self.__read_file(testee.get_full_file_path("README.md"))
            self.assertEqual("master branch readme", readme)

            self.assertFalse(Path(testee.get_full_file_path("../credentials.sh")).exists())
        logging_mock.info.assert_called_once_with("Cloning repository: %s", self.__mock_repo_api.get_clone_url())

    @patch("gitopscli.git_api.git_repo.logging")
    def test_clone_with_credentials(self, logging_mock):
        self.__mock_repo_api.get_username.return_value = "User"
        self.__mock_repo_api.get_password.return_value = "Pass"
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            credentials_file = self.__read_file(testee.get_full_file_path("../credentials.sh"))
            self.assertEqual(
                """\
#!/bin/sh
echo username='User'
echo password='Pass'
""",
                credentials_file,
            )
        logging_mock.info.assert_called_once_with("Cloning repository: %s", self.__mock_repo_api.get_clone_url())

    @patch("gitopscli.git_api.git_repo.logging")
    def test_clone_unknown_url(self, logging_mock):
        self.__mock_repo_api.get_clone_url.return_value = "invalid_url"
        with GitRepo(self.__mock_repo_api) as testee:
            with pytest.raises(GitOpsException) as ex:
                testee.clone()
            self.assertEqual("Error cloning 'invalid_url'", str(ex.value))
        logging_mock.info.assert_called_once_with("Cloning repository: %s", self.__mock_repo_api.get_clone_url())

    def test_clone_with_depth_1(self):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            # Verify that the repository was cloned with depth 1
            repo = Repo(testee.get_full_file_path("."))
            # A shallow clone with depth 1 should only have the latest commit
            commits = list(repo.iter_commits("master"))
            self.assertEqual(1, len(commits), "Clone should be shallow with depth 1")

    def test_get_full_file_path(self):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            self.assertRegex(
                testee.get_full_file_path("foo.bar"),
                r"^/tmp/gitopscli/[0-9a-f\-]+/repo/foo\.bar$",
            )

    @patch("gitopscli.git_api.git_repo.logging")
    def test_new_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            logging_mock.reset_mock()

            testee.new_branch("foo")

            repo = Repo(testee.get_full_file_path("."))
            branches = [str(b) for b in repo.branches]
            self.assertIn("foo", branches)
        logging_mock.info.assert_called_once_with("Creating new branch: %s", "foo")

    @patch("gitopscli.git_api.git_repo.logging")
    def test_new_branch_name_collision(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            logging_mock.reset_mock()

            with pytest.raises(GitOpsException) as ex:
                testee.new_branch("master")
            self.assertEqual("Error creating new branch 'master'.", str(ex.value))
        logging_mock.info.assert_called_once_with("Creating new branch: %s", "master")

    @patch("gitopscli.git_api.git_repo.logging")
    def test_commit(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            logging_mock.reset_mock()

            with Path(testee.get_full_file_path("foo.md")).open("w") as outfile:
                outfile.write("new file")
            with Path(testee.get_full_file_path("README.md")).open("w") as outfile:
                outfile.write("new content")

            commit_hash = testee.commit(
                git_user="john doe",
                git_email="john@doe.com",
                git_author_name=None,
                git_author_email=None,
                message="new commit",
            )
            repo = Repo(testee.get_full_file_path("."))
            commits = list(repo.iter_commits("master"))

            self.assertIsNotNone(commit_hash)
            self.assertRegex(commit_hash, "^[a-f0-9]{40}$", "Not a long commit hash")
            self.assertEqual(2, len(commits))
            self.assertEqual("new commit\n", commits[0].message)
            self.assertEqual("john doe", commits[0].committer.name)
            self.assertEqual("john@doe.com", commits[0].committer.email)
            self.assertEqual("john doe", commits[0].author.name)
            self.assertEqual("john@doe.com", commits[0].author.email)
            self.assertIn("foo.md", commits[0].stats.files)
            self.assertIn("README.md", commits[0].stats.files)
        logging_mock.info.assert_called_once_with("Creating commit with message: %s", "new commit")

    @patch("gitopscli.git_api.git_repo.logging")
    def test_commit_with_custom_author(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            logging_mock.reset_mock()

            with Path(testee.get_full_file_path("foo.md")).open("w") as outfile:
                outfile.write("new file")
            with Path(testee.get_full_file_path("README.md")).open("w") as outfile:
                outfile.write("new content")

            commit_hash = testee.commit(
                git_user="john doe",
                git_email="john@doe.com",
                git_author_name="custom author",
                git_author_email="custom@author.com",
                message="new commit",
            )
            repo = Repo(testee.get_full_file_path("."))
            commits = list(repo.iter_commits("master"))

            self.assertIsNotNone(commit_hash)
            self.assertRegex(commit_hash, "^[a-f0-9]{40}$", "Not a long commit hash")
            self.assertEqual(2, len(commits))
            self.assertEqual("new commit\n", commits[0].message)
            self.assertEqual("john doe", commits[0].committer.name)
            self.assertEqual("john@doe.com", commits[0].committer.email)
            self.assertEqual("custom author", commits[0].author.name)
            self.assertEqual("custom@author.com", commits[0].author.email)
            self.assertIn("foo.md", commits[0].stats.files)
            self.assertIn("README.md", commits[0].stats.files)
        logging_mock.info.assert_called_once_with("Creating commit with message: %s", "new commit")

    def test_commit_with_custom_author_name_but_no_email_returns_validation_error(self):
        with GitRepo(self.__mock_repo_api) as testee:
            with pytest.raises(GitOpsException) as ex:
                testee.commit(
                    git_user="john doe",
                    git_email="john@doe.com",
                    git_author_name="custom author",
                    git_author_email="",  # missing
                    message="new commit",
                )
            assert str(ex.value).startswith(
                "Please provide the name and email address of the Git author or provide neither!"
            )

    def test_commit_with_custom_author_email_but_no_name_returns_validation_error(self):
        with GitRepo(self.__mock_repo_api) as testee:
            with pytest.raises(GitOpsException) as ex:
                testee.commit(
                    git_user="john doe",
                    git_email="john@doe.com",
                    git_author_name="",  # missing
                    git_author_email="custom@author.com",
                    message="new commit",
                )
            assert str(ex.value).startswith(
                "Please provide the name and email address of the Git author or provide neither!"
            )

    @patch("gitopscli.git_api.git_repo.logging")
    def test_commit_nothing_to_commit(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            logging_mock.reset_mock()

            commit_hash = testee.commit(
                git_user="john doe",
                git_email="john@doe.com",
                git_author_name=None,
                git_author_email=None,
                message="empty commit",
            )
            repo = Repo(testee.get_full_file_path("."))
            commits = list(repo.iter_commits("master"))

            self.assertIsNone(commit_hash)
            self.assertEqual(1, len(commits))
            self.assertEqual("initial commit\n", commits[0].message)
        logging_mock.assert_not_called()

    @patch("gitopscli.git_api.git_repo.logging")
    def test_pull_rebase_master_single_commit(self, logging_mock):
        origin_repo = self.__origin
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            # local commit
            with Path(testee.get_full_file_path("local.md")).open("w") as outfile:
                outfile.write("local file")
            local_repo = Repo(testee.get_full_file_path("."))
            local_repo.git.add("--all")
            local_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
            local_repo.git.commit("-m", "local commit")

            # origin commit
            with Path(f"{origin_repo.working_dir}/origin.md").open("w") as readme:
                readme.write("origin file")
            origin_repo.git.add("--all")
            origin_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
            origin_repo.git.commit("-m", "origin commit")

            # pull and rebase from remote
            logging_mock.reset_mock()

            testee.pull_rebase()

            logging_mock.info.assert_called_once_with("Pull and rebase: %s", "master")

            # then push should work
            testee.push()

            commits = list(self.__origin.iter_commits("master"))
            self.assertEqual(3, len(commits))
            self.assertEqual("initial commit\n", commits[2].message)
            self.assertEqual("origin commit\n", commits[1].message)
            self.assertEqual("local commit\n", commits[0].message)

    @patch("gitopscli.git_api.git_repo.logging")
    def test_pull_rebase_remote_branch_single_commit(self, logging_mock):
        origin_repo = self.__origin
        origin_repo.git.checkout("xyz")
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone(branch="xyz")

            # local commit
            with Path(testee.get_full_file_path("local.md")).open("w") as outfile:
                outfile.write("local file")
            local_repo = Repo(testee.get_full_file_path("."))
            local_repo.git.add("--all")
            local_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
            local_repo.git.commit("-m", "local branch commit")

            # origin commit
            with Path(f"{origin_repo.working_dir}/origin.md").open("w") as readme:
                readme.write("origin file")
            origin_repo.git.add("--all")
            origin_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
            origin_repo.git.commit("-m", "origin branch commit")

            # pull and rebase from remote
            logging_mock.reset_mock()

            testee.pull_rebase()

            logging_mock.info.assert_called_once_with("Pull and rebase: %s", "xyz")

            # then push should work
            testee.push()

            commits = list(self.__origin.iter_commits("xyz"))
            self.assertEqual(4, len(commits))
            self.assertEqual("local branch commit\n", commits[0].message)
            self.assertEqual("origin branch commit\n", commits[1].message)
            self.assertEqual("initial xyz branch commit\n", commits[2].message)

    @patch("gitopscli.git_api.git_repo.logging")
    def test_pull_rebase_without_new_commits(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            # pull and rebase from remote
            logging_mock.reset_mock()

            testee.pull_rebase()

            logging_mock.info.assert_called_once_with("Pull and rebase: %s", "master")

    @patch("gitopscli.git_api.git_repo.logging")
    def test_pull_rebase_if_no_remote_branch_is_noop(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            testee.new_branch("new-branch-only-local")

            # pull and rebase from remote
            logging_mock.reset_mock()

            testee.pull_rebase()

            logging_mock.assert_not_called()

    @patch("gitopscli.git_api.git_repo.logging")
    def test_push(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            with Path(testee.get_full_file_path("foo.md")).open("w") as readme:
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

    @patch("gitopscli.git_api.git_repo.logging")
    def test_push_no_changes(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            logging_mock.reset_mock()

            testee.push("master")
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "master")

    @patch("gitopscli.git_api.git_repo.logging")
    def test_push_current_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            testee.new_branch("foo")
            logging_mock.reset_mock()

            testee.push()  # current branch
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "foo")

    @patch("gitopscli.git_api.git_repo.logging")
    def test_push_unknown_branch(self, logging_mock):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            logging_mock.reset_mock()

            with pytest.raises(GitOpsException) as ex:
                testee.push("unknown")
            assert str(ex.value).startswith("Error pushing branch 'unknown' to origin")
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "unknown")

    @patch("gitopscli.git_api.git_repo.logging")
    def test_push_commit_hook_error_reason_is_shown(self, logging_mock):
        repo_dir = self.__origin.working_dir
        with Path(f"{repo_dir}/.git/hooks/pre-receive").open("w") as pre_receive_hook:
            pre_receive_hook.write('echo >&2 "we reject this push"; exit 1')
        Path(
            f"{repo_dir}/.git/hooks/pre-receive",
        ).chmod(
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR,
        )

        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()

            with Path(testee.get_full_file_path("foo.md")).open("w") as readme:
                readme.write("new file")
            util_repo = Repo(testee.get_full_file_path("."))
            util_repo.git.add("--all")
            util_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
            util_repo.git.commit("-m", "new commit")

            logging_mock.reset_mock()

            with pytest.raises(GitOpsException) as ex:
                testee.push("master")
            assert "pre-receive" in str(ex.value)
            assert "we reject this push" in str(ex.value)
        logging_mock.info.assert_called_once_with("Pushing branch: %s", "master")

    def test_get_author_from_last_commit(self):
        with GitRepo(self.__mock_repo_api) as testee:
            testee.clone()
            self.assertEqual("unit tester <unit@tester.com>", testee.get_author_from_last_commit())

    def test_get_author_from_last_commit_not_cloned_yet(self):
        with GitRepo(self.__mock_repo_api) as testee, pytest.raises(GitOpsException) as ex:
            testee.get_author_from_last_commit()
        self.assertEqual("Repository not cloned yet!", str(ex.value))

from os import path, makedirs, chmod
import stat
import unittest
import uuid
from pathlib import Path
from git import Repo
import pytest

from gitopscli.git.abstract_git_util import AbstractGitUtil
from gitopscli.gitops_exception import GitOpsException


class GitUtil(AbstractGitUtil):
    _clone_url = None

    def set_clone_url(self, clone_url):
        self._clone_url = clone_url

    def get_clone_url(self):
        return self._clone_url

    def create_pull_request(self, from_branch, to_branch, title, description):
        pass

    def get_pull_request_url(self, pull_request):
        pass

    def merge_pull_request(self, pull_request):
        pass

    def add_pull_request_comment(self, pr_id, text, parent_id):
        pass

    def delete_branch(self, branch):
        pass

    def get_pull_request_branch(self, pr_id):
        pass


class AbstractGitUtilTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = self._create_tmp_dir()
        self.origin = self._create_origin()

    @staticmethod
    def _create_tmp_dir():
        tmp_dir_path = f"/tmp/gitopscli-test-{uuid.uuid4()}"
        makedirs(tmp_dir_path)
        return tmp_dir_path

    def _read_file(self, filename):
        self.assertTrue(filename)
        with open(filename) as input_stream:
            return input_stream.read()

    @staticmethod
    def _create_origin():
        repo_dir = AbstractGitUtilTest._create_tmp_dir()

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

    def test_checkout_without_credentials(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        readme = self._read_file(f"{self.tmp_dir}/repo/README.md")
        self.assertEqual("master branch readme", readme)

        self.assertFalse(path.exists(f"{self.tmp_dir}/credentials.sh"))

    def test_checkout_with_credentials(self):
        testee = GitUtil(self.tmp_dir, username="USER", password="PASS", git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        credentials_file = self._read_file(f"{self.tmp_dir}/credentials.sh")
        self.assertEqual(
            """\
#!/bin/sh
echo username=USER
echo password=PASS
""",
            credentials_file,
        )

    def test_checkout_branch(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("xyz")
        readme = self._read_file(f"{self.tmp_dir}/repo/README.md")
        self.assertEqual("xyz branch readme", readme)

    def test_checkout_unknown_url(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url("invalid_url")
        with pytest.raises(GitOpsException) as ex:
            testee.checkout("master")
        self.assertEqual("Error cloning 'invalid_url'", str(ex.value))

    def test_checkout_unknown_branch(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        with pytest.raises(GitOpsException) as ex:
            testee.checkout("foo")
        self.assertEqual("Error checking out branch 'foo'", str(ex.value))

    def test_get_full_file_path(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")
        self.assertEqual(Path(f"{self.tmp_dir}/repo/foo.bar"), testee.get_full_file_path("foo.bar"))

    def test_new_branch(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        testee.new_branch("foo")

        repo = Repo(f"{self.tmp_dir}/repo")
        branches = [str(b) for b in repo.branches]
        self.assertIn("foo", branches)

    def test_new_branch_name_collision(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        with pytest.raises(GitOpsException) as ex:
            testee.new_branch("xyz")
        self.assertEqual("Error creating new branch 'xyz'.", str(ex.value))

    def test_commit(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user="john doe", git_email="john@doe.com")
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        with open(f"{self.tmp_dir}/repo/foo.md", "w") as foo:
            foo.write("new file")
        with open(f"{self.tmp_dir}/repo/README.md", "w") as readme:
            readme.write("new content")
        testee.commit("new commit")

        repo = Repo(f"{self.tmp_dir}/repo")
        commits = list(repo.iter_commits("master"))
        self.assertEqual(2, len(commits))
        self.assertEqual("new commit\n", commits[0].message)
        self.assertEqual("john doe", commits[0].author.name)
        self.assertEqual("john@doe.com", commits[0].author.email)
        self.assertIn("foo.md", commits[0].stats.files)
        self.assertIn("README.md", commits[0].stats.files)

    def test_commit_nothing_to_commit(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        testee.commit("empty commit")

        repo = Repo(f"{self.tmp_dir}/repo")
        commits = list(repo.iter_commits("master"))
        self.assertEqual(1, len(commits))
        self.assertEqual("initial commit\n", commits[0].message)

    def test_push(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        with open(f"{self.tmp_dir}/repo/foo.md", "w") as readme:
            readme.write("new file")
        util_repo = Repo(f"{self.tmp_dir}/repo")
        util_repo.git.add("--all")
        util_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
        util_repo.git.commit("-m", "new commit")

        testee.push("master")

        commits = list(self.origin.iter_commits("master"))
        self.assertEqual(2, len(commits))
        self.assertEqual("new commit\n", commits[0].message)

    def test_push_no_changes(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        testee.push("master")

    def test_push_unknown_branch(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        with pytest.raises(GitOpsException) as ex:
            testee.push("unknown")
        assert str(ex.value).startswith("Error pushing branch 'unknown' to origin")

    def test_push_commit_hook_error_reason_is_shown(self):
        repo_dir = self.origin.working_dir
        with open(f"{repo_dir}/.git/hooks/pre-receive", "w") as pre_receive_hook:
            pre_receive_hook.write("echo >&2 \"we reject this push\"; exit 1")
        chmod(f"{repo_dir}/.git/hooks/pre-receive", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        with open(f"{self.tmp_dir}/repo/foo.md", "w") as readme:
            readme.write("new file")
        util_repo = Repo(f"{self.tmp_dir}/repo")
        util_repo.git.add("--all")
        util_repo.config_writer().set_value("user", "email", "unit@tester.com").release()
        util_repo.git.commit("-m", "new commit")

        with pytest.raises(GitOpsException) as ex:
            testee.push("master")
        assert "pre-receive" in str(ex.value) and "we reject this push" in str(ex.value)

    def test_get_author_from_last_commit(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        self.assertEqual("unit tester <unit@tester.com>", testee.get_author_from_last_commit())

    def test_get_last_commit_hash(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("xyz")

        self.assertEqual(self.origin.head.commit.hexsha, testee.get_last_commit_hash())

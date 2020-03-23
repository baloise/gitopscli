import shutil
import unittest
import uuid
import pytest
from os import path, makedirs
from git import Repo

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

        repo = Repo().init(repo_dir)
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
        self.assertEqual(f"Error cloning 'invalid_url'", str(ex.value))

    def test_checkout_unknown_branch(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        with pytest.raises(GitOpsException) as ex:
            testee.checkout("foo")
        self.assertEqual(f"Error checking out branch 'foo'", str(ex.value))

    def test_new_branch(self):
        testee = GitUtil(self.tmp_dir, username=None, password=None, git_user=None, git_email=None)
        testee.set_clone_url(self.origin.working_dir)
        testee.checkout("master")

        testee.new_branch("foo")

        branches = [str(x) for x in Repo(f"{self.tmp_dir}/repo").branches]
        self.assertIn("foo", branches)

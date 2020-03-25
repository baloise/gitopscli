from os import path, makedirs
import unittest
from unittest.mock import patch, MagicMock
import uuid
from pathlib import Path
from git import Repo
import pytest

from gitopscli.gitops_exception import GitOpsException
from gitopscli.git.create_git import create_git


class CreateGitTest(unittest.TestCase):
    @patch("gitopscli.git.create_git.GithubGitUtil")
    def test_github(self, mock_github_git_util_constructor):
        mock_github_git_util = MagicMock()
        mock_github_git_util_constructor.return_value = mock_github_git_util

        git = create_git(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )

        self.assertEqual(git, mock_github_git_util)
        mock_github_git_util_constructor.assert_called_with(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
        )

    @patch("gitopscli.git.create_git.GithubGitUtil")
    def test_github_via_git_provider_url(self, mock_github_git_util_constructor):
        mock_github_git_util = MagicMock()
        mock_github_git_util_constructor.return_value = mock_github_git_util

        git = create_git(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
            git_provider=None,
            git_provider_url="www.github.com",
        )

        self.assertEqual(git, mock_github_git_util)
        mock_github_git_util_constructor.assert_called_with(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
        )

    @patch("gitopscli.git.create_git.BitBucketGitUtil")
    def test_bitbucket_server(self, mock_bitbucket_git_util_constructor):
        mock_bitbucket_git_util = MagicMock()
        mock_bitbucket_git_util_constructor.return_value = mock_bitbucket_git_util

        git = create_git(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
            git_provider="bitbucket-server",
            git_provider_url="GIT_PROVIDER_URL",
        )

        self.assertEqual(git, mock_bitbucket_git_util)
        mock_bitbucket_git_util_constructor.assert_called_with(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
            git_provider_url="GIT_PROVIDER_URL",
        )

    def test_bitbucket_server_missing_git_provider_url(self):
        with pytest.raises(GitOpsException) as ex:
            create_git(
                tmp_dir="TMP_DIR",
                username="USER",
                password="PASS",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORG",
                repository_name="REPO",
                git_provider="bitbucket-server",
                git_provider_url=None,  # <- missing
            )
        self.assertEqual("Please provide --git-provider-url for bitbucket-server", str(ex.value))

    @patch("gitopscli.git.create_git.BitBucketGitUtil")
    def test_bitbucket_server_via_git_provider_url(self, mock_bitbucket_git_util_constructor):
        mock_bitbucket_git_util = MagicMock()
        mock_bitbucket_git_util_constructor.return_value = mock_bitbucket_git_util

        git = create_git(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
            git_provider=None,
            git_provider_url="bitbucket.baloise.dev",
        )

        self.assertEqual(git, mock_bitbucket_git_util)
        mock_bitbucket_git_util_constructor.assert_called_with(
            tmp_dir="TMP_DIR",
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
            git_provider_url="bitbucket.baloise.dev",
        )

    def test_unknown_git_provider(self):
        with pytest.raises(GitOpsException) as ex:
            create_git(
                tmp_dir="TMP_DIR",
                username="USER",
                password="PASS",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORG",
                repository_name="REPO",
                git_provider="unknown",  # <- unknown
                git_provider_url="GIT_PROVIDER_URL",
            )
        self.assertEqual("Git provider 'unknown' is not supported.", str(ex.value))

    def test_cannot_infer_git_provider_from_url(self):
        with pytest.raises(GitOpsException) as ex:
            create_git(
                tmp_dir="TMP_DIR",
                username="USER",
                password="PASS",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORG",
                repository_name="REPO",
                git_provider=None,
                git_provider_url="some.unknown-url.com",
            )
        self.assertEqual("Please provide --git-provider", str(ex.value))

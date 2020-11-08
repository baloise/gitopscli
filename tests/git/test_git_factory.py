import unittest
from unittest.mock import patch, MagicMock
import pytest

from gitopscli.gitops_exception import GitOpsException
from gitopscli.git import create_git, GitConfig


class CreateGitTest(unittest.TestCase):
    @patch("gitopscli.git.git_factory.GithubGitUtil")
    def test_github(self, mock_github_git_util_constructor):
        mock_github_git_util = MagicMock()
        mock_github_git_util_constructor.return_value = mock_github_git_util

        git = create_git(
            git_config=GitConfig(
                username="USER",
                password="PASS",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                git_provider="github",
                git_provider_url=None,
            ),
            organisation="ORG",
            repository_name="REPO",
        )

        self.assertEqual(git, mock_github_git_util)
        mock_github_git_util_constructor.assert_called_with(
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
        )

    @patch("gitopscli.git.git_factory.GithubGitUtil")
    def test_github_via_git_provider_url(self, mock_github_git_util_constructor):
        mock_github_git_util = MagicMock()
        mock_github_git_util_constructor.return_value = mock_github_git_util

        git = create_git(
            git_config=GitConfig(
                username="USER",
                password="PASS",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                git_provider=None,
                git_provider_url="www.github.com",
            ),
            organisation="ORG",
            repository_name="REPO",
        )

        self.assertEqual(git, mock_github_git_util)
        mock_github_git_util_constructor.assert_called_with(
            username="USER",
            password="PASS",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            organisation="ORG",
            repository_name="REPO",
        )

    @patch("gitopscli.git.git_factory.BitBucketGitUtil")
    def test_bitbucket_server(self, mock_bitbucket_git_util_constructor):
        mock_bitbucket_git_util = MagicMock()
        mock_bitbucket_git_util_constructor.return_value = mock_bitbucket_git_util

        git = create_git(
            git_config=GitConfig(
                username="USER",
                password="PASS",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                git_provider="bitbucket-server",
                git_provider_url="GIT_PROVIDER_URL",
            ),
            organisation="ORG",
            repository_name="REPO",
        )

        self.assertEqual(git, mock_bitbucket_git_util)
        mock_bitbucket_git_util_constructor.assert_called_with(
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
                git_config=GitConfig(
                    username="USER",
                    password="PASS",
                    git_user="GIT_USER",
                    git_email="GIT_EMAIL",
                    git_provider="bitbucket-server",
                    git_provider_url=None,  # <- missing
                ),
                organisation="ORG",
                repository_name="REPO",
            )
        self.assertEqual("Please provide url for bitbucket-server.", str(ex.value))

    @patch("gitopscli.git.git_factory.BitBucketGitUtil")
    def test_bitbucket_server_via_git_provider_url(self, mock_bitbucket_git_util_constructor):
        mock_bitbucket_git_util = MagicMock()
        mock_bitbucket_git_util_constructor.return_value = mock_bitbucket_git_util

        git = create_git(
            git_config=GitConfig(
                username="USER",
                password="PASS",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                git_provider=None,
                git_provider_url="bitbucket.baloise.dev",
            ),
            organisation="ORG",
            repository_name="REPO",
        )

        self.assertEqual(git, mock_bitbucket_git_util)
        mock_bitbucket_git_util_constructor.assert_called_with(
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
                git_config=GitConfig(
                    username="USER",
                    password="PASS",
                    git_user="GIT_USER",
                    git_email="GIT_EMAIL",
                    git_provider="unknown",  # <- unknown
                    git_provider_url="GIT_PROVIDER_URL",
                ),
                organisation="ORG",
                repository_name="REPO",
            )
        self.assertEqual("Git provider 'unknown' is not supported.", str(ex.value))

    def test_cannot_infer_git_provider_from_url(self):
        with pytest.raises(GitOpsException) as ex:
            create_git(
                git_config=GitConfig(
                    username="USER",
                    password="PASS",
                    git_user="GIT_USER",
                    git_email="GIT_EMAIL",
                    git_provider=None,
                    git_provider_url="some.unknown-url.com",
                ),
                organisation="ORG",
                repository_name="REPO",
            )
        self.assertEqual(
            "Unknown git provider url: 'some.unknown-url.com'. Please specify git provider.", str(ex.value)
        )

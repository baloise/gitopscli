import unittest
from unittest.mock import patch, MagicMock

from gitopscli.gitops_exception import GitOpsException
from gitopscli.git_api import GitRepoApiFactory, GitApiConfig, GitProvider


class GitRepoApiFactoryTest(unittest.TestCase):
    @patch("gitopscli.git_api.git_repo_api_factory.GitRepoApiLoggingProxy")
    @patch("gitopscli.git_api.git_repo_api_factory.GithubGitRepoApiAdapter")
    def test_create_github(self, mock_github_adapter_constructor, mock_logging_proxy_constructor):
        mock_github_adapter = MagicMock()
        mock_github_adapter_constructor.return_value = mock_github_adapter

        mock_logging_proxy = MagicMock()
        mock_logging_proxy_constructor.return_value = mock_logging_proxy

        git_repo_api = GitRepoApiFactory.create(
            config=GitApiConfig(
                username="USER", password="PASS", git_provider=GitProvider.GITHUB, git_provider_url=None,
            ),
            organisation="ORG",
            repository_name="REPO",
        )

        self.assertEqual(git_repo_api, mock_logging_proxy)

        mock_github_adapter_constructor.assert_called_with(
            username="USER", password="PASS", organisation="ORG", repository_name="REPO",
        )
        mock_logging_proxy_constructor.assert_called_with(mock_github_adapter)

    @patch("gitopscli.git_api.git_repo_api_factory.GitRepoApiLoggingProxy")
    @patch("gitopscli.git_api.git_repo_api_factory.BitbucketGitRepoApiAdapter")
    def test_create_bitbucket(self, mock_bitbucket_adapter_constructor, mock_logging_proxy_constructor):
        mock_bitbucket_adapter = MagicMock()
        mock_bitbucket_adapter_constructor.return_value = mock_bitbucket_adapter

        mock_logging_proxy = MagicMock()
        mock_logging_proxy_constructor.return_value = mock_logging_proxy

        git_repo_api = GitRepoApiFactory.create(
            config=GitApiConfig(
                username="USER", password="PASS", git_provider=GitProvider.BITBUCKET, git_provider_url="PROVIDER_URL",
            ),
            organisation="ORG",
            repository_name="REPO",
        )

        self.assertEqual(git_repo_api, mock_logging_proxy)

        mock_bitbucket_adapter_constructor.assert_called_with(
            git_provider_url="PROVIDER_URL",
            username="USER",
            password="PASS",
            organisation="ORG",
            repository_name="REPO",
        )
        mock_logging_proxy_constructor.assert_called_with(mock_bitbucket_adapter)

    def test_create_bitbucket_missing_url(self):
        try:
            GitRepoApiFactory.create(
                config=GitApiConfig(
                    username="USER", password="PASS", git_provider=GitProvider.BITBUCKET, git_provider_url=None,
                ),
                organisation="ORG",
                repository_name="REPO",
            )
            self.fail("Expected a GitOpsException")
        except GitOpsException as ex:
            self.assertEqual("Please provide url for Bitbucket!", str(ex))

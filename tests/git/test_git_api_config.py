import unittest

from gitopscli.gitops_exception import GitOpsException
from gitopscli.git import GitApiConfig


class GitApiConfigTest(unittest.TestCase):
    def test_is_provider_bitbucket(self):
        git_api_config = GitApiConfig(
            username=None, password=None, git_provider="bitbucket-server", git_provider_url=None
        )
        self.assertTrue(git_api_config.is_provider_bitbucket)

        git_api_config = GitApiConfig(
            username=None, password=None, git_provider="some-other-provider", git_provider_url=None
        )
        self.assertFalse(git_api_config.is_provider_bitbucket)

    def test_is_provider_bitbucket_from_url(self):
        git_api_config = GitApiConfig(
            username=None, password=None, git_provider=None, git_provider_url="http://my-bitbucket-url.com/"
        )
        self.assertTrue(git_api_config.is_provider_bitbucket)

        git_api_config = GitApiConfig(
            username=None, password=None, git_provider=None, git_provider_url="http://some-random-url.com/"
        )
        try:
            _ = git_api_config.is_provider_bitbucket
            self.fail("expected GitOpsCl")
        except GitOpsException as ex:
            self.assertEqual(
                "Unknown git provider url: 'http://some-random-url.com/'. Please specify git provider.", str(ex)
            )

    def test_is_provider_github(self):
        git_api_config = GitApiConfig(username=None, password=None, git_provider="github", git_provider_url=None)
        self.assertTrue(git_api_config.is_provider_github)

        git_api_config = GitApiConfig(
            username=None, password=None, git_provider="some-other-provider", git_provider_url=None
        )
        self.assertFalse(git_api_config.is_provider_github)

    def test_is_provider_github_from_url(self):
        git_api_config = GitApiConfig(
            username=None, password=None, git_provider=None, git_provider_url="https://github.com/"
        )
        self.assertTrue(git_api_config.is_provider_github)

        git_api_config = GitApiConfig(
            username=None, password=None, git_provider=None, git_provider_url="http://some-random-url.com/"
        )
        try:
            _ = git_api_config.is_provider_github
            self.fail("expected GitOpsCl")
        except GitOpsException as ex:
            self.assertEqual(
                "Unknown git provider url: 'http://some-random-url.com/'. Please specify git provider.", str(ex)
            )

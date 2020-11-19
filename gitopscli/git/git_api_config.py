from typing import NamedTuple
from gitopscli.gitops_exception import GitOpsException


class GitApiConfig(NamedTuple):
    username: str
    password: str
    git_provider: str
    git_provider_url: str

    @property
    def is_provider_bitbucket(self) -> bool:
        return (self.git_provider or self.__git_provider_from_url()) == "bitbucket-server"

    @property
    def is_provider_github(self) -> bool:
        return (self.git_provider or self.__git_provider_from_url()) == "github"

    def __git_provider_from_url(self) -> str:
        if "bitbucket" in self.git_provider_url:
            return "bitbucket-server"
        if "github" in self.git_provider_url:
            return "github"
        raise GitOpsException(f"Unknown git provider url: '{self.git_provider_url}'. Please specify git provider.")

from dataclasses import dataclass

from .git_provider import GitProvider


@dataclass(frozen=True)
class GitApiConfig:
    username: str
    password: str
    git_provider: GitProvider
    git_provider_url: str | None

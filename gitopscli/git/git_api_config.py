from dataclasses import dataclass
from typing import Optional
from .git_provider import GitProvider


@dataclass(frozen=True)
class GitApiConfig:
    username: str
    password: str
    git_provider: GitProvider
    git_provider_url: Optional[str]

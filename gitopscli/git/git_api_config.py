from typing import NamedTuple, Optional
from .git_provider import GitProvider


class GitApiConfig(NamedTuple):
    username: str
    password: str
    git_provider: GitProvider
    git_provider_url: Optional[str]

from enum import Enum, auto


class GitProvider(Enum):
    GITHUB = auto()
    BITBUCKET = auto()
    BITBUCKET_CLOUD = auto()
    GITLAB = auto()

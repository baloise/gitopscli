from enum import Enum, auto


class GitProvider(Enum):
    GITHUB = auto()
    BITBUCKET = auto()
    GITLAB = auto()
    AZURE_DEVOPS = auto()

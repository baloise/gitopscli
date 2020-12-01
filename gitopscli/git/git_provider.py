from enum import Flag, auto


class GitProvider(Flag):
    GITHUB = auto()
    BITBUCKET = auto()

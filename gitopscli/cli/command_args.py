from typing import Any, NamedTuple, Union, Optional


class DeployArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    file: str
    values: Any

    single_commit: bool
    commit_message: Optional[str]

    create_pr: bool
    auto_merge: bool


class SyncAppsArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    root_organisation: str
    root_repository_name: str


class AddPrCommentArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    organisation: str
    repository_name: str

    pr_id: int
    parent_id: Optional[int]
    text: str


class CreatePreviewArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    git_hash: str
    preview_id: str


class CreatePrPreviewArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    pr_id: int
    parent_id: Optional[int]


class DeletePrPreviewArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    branch: str
    expect_preview_exists: bool


class DeletePreviewArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    preview_id: str
    expect_preview_exists: bool


class VersionArgs(NamedTuple):
    pass


CommandArgs = Union[
    DeployArgs,
    SyncAppsArgs,
    AddPrCommentArgs,
    CreatePreviewArgs,
    CreatePrPreviewArgs,
    DeletePreviewArgs,
    DeletePrPreviewArgs,
    VersionArgs,
]

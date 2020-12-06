from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io.yaml_util import yaml_file_load


def load_gitops_config(git_api_config: GitApiConfig, organisation: str, repository_name: str) -> GitOpsConfig:
    git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name)
    with GitRepo(git_repo_api) as git_repo:
        git_repo.checkout("master")
        gitops_config_file_path = git_repo.get_full_file_path(".gitops.config.yaml")
        try:
            gitops_config_yaml = yaml_file_load(gitops_config_file_path)
        except FileNotFoundError as ex:
            raise GitOpsException("No such file: .gitops.config.yaml") from ex
    return GitOpsConfig.from_yaml(gitops_config_yaml)

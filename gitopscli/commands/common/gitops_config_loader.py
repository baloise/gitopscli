import logging
from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.io.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException


def load_gitops_config(git_api_config: GitApiConfig, organisation: str, repository_name: str) -> GitOpsConfig:
    git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name)
    with GitRepo(git_repo_api) as git_repo:
        logging.info("Checkout '%s/%s' branch 'master'...", organisation, repository_name)
        git_repo.checkout("master")

        logging.info("Reading '.gitops.config.yaml'...")
        try:
            return GitOpsConfig(git_repo.get_full_file_path(".gitops.config.yaml"))
        except FileNotFoundError as ex:
            raise GitOpsException("No such file: .gitops.config.yaml") from ex

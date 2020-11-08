import logging
from gitopscli.git import create_git, GitConfig
from gitopscli.io.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException


def load_gitops_config(git_config: GitConfig, organisation: str, repository_name: str) -> GitOpsConfig:
    with create_git(git_config, organisation, repository_name) as git:
        logging.info("Checkout '%s/%s' branch 'master'...", organisation, repository_name)
        git.checkout("master")

        logging.info("Reading '.gitops.config.yaml'...")
        try:
            return GitOpsConfig(git.get_full_file_path(".gitops.config.yaml"))
        except FileNotFoundError as ex:
            raise GitOpsException("No such file: .gitops.config.yaml") from ex

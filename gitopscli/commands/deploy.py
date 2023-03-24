import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Literal, List
from gitopscli.git_api import GitApiConfig, GitRepo, GitRepoApi, GitRepoApiFactory
from gitopscli.io_api.yaml_util import update_yaml_file, yaml_dump, YAMLException
from gitopscli.gitops_exception import GitOpsException
from .command import Command


class DeployCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
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
        json: bool

        pr_labels: Optional[List[str]]
        merge_parameters: Optional[Any]
        merge_method: Literal["squash", "rebase", "merge"] = "merge"

    def __init__(self, args: Args) -> None:
        self.__args = args
        self.__commit_hashes: List[str] = []

    def execute(self) -> None:
        git_repo_api = self.__create_git_repo_api()
        with GitRepo(git_repo_api) as git_repo:
            git_repo.clone()

            if self.__args.create_pr:
                pr_branch = f"gitopscli-deploy-{str(uuid.uuid4())[:8]}"
                git_repo.new_branch(pr_branch)

            updated_values = self.__update_values(git_repo)
            if not updated_values:
                logging.info("All values already up-to-date. I'm done here.")
                return

            git_repo.push()

        if self.__args.create_pr:
            title, description = self.__create_pull_request_title_and_description(updated_values)
            pr_id = git_repo_api.create_pull_request_to_default_branch(pr_branch, title, description).pr_id
            if self.__args.pr_labels:
                git_repo_api.add_pull_request_label(pr_id, self.__args.pr_labels)
            if self.__args.auto_merge:
                if self.__args.merge_parameters:
                    git_repo_api.merge_pull_request(pr_id, self.__args.merge_method, self.__args.merge_parameters)
                else:
                    git_repo_api.merge_pull_request(pr_id, self.__args.merge_method)
                git_repo_api.delete_branch(pr_branch)

        if self.__args.json:
            print(json.dumps({"commits": [{"hash": h} for h in self.__commit_hashes]}, indent=4))

    def __create_git_repo_api(self) -> GitRepoApi:
        return GitRepoApiFactory.create(self.__args, self.__args.organisation, self.__args.repository_name)

    def __update_values(self, git_repo: GitRepo) -> Dict[str, Any]:
        args = self.__args
        single_commit = args.single_commit or args.commit_message
        full_file_path = git_repo.get_full_file_path(args.file)
        updated_values = {}
        for key, value in args.values.items():
            try:
                updated_value = update_yaml_file(full_file_path, key, value)
            except (FileNotFoundError, IsADirectoryError) as ex:
                raise GitOpsException(f"No such file: {args.file}") from ex
            except YAMLException as ex:
                raise GitOpsException(f"Error loading file: {args.file}") from ex
            except KeyError as ex:
                raise GitOpsException(str(ex)) from ex

            if not updated_value:
                logging.info("Yaml property %s already up-to-date", key)
                continue

            logging.info("Updated yaml property %s to %s", key, value)
            updated_values[key] = value

            if not single_commit:
                self.__commit(git_repo, f"changed '{key}' to '{value}' in {args.file}")

        if single_commit and updated_values:
            if args.commit_message:
                message = args.commit_message
            elif len(updated_values) == 1:
                key, value = list(updated_values.items())[0]
                message = f"changed '{key}' to '{value}' in {args.file}"
            else:
                updates_count = len(updated_values)
                message = f"updated {updates_count} value{'s' if updates_count > 1 else ''} in {args.file}"
                message += f"\n\n{yaml_dump(updated_values)}"
            self.__commit(git_repo, message)

        return updated_values

    def __create_pull_request_title_and_description(self, updated_values: Dict[str, Any]) -> Tuple[str, str]:
        updated_file_name = self.__args.file
        updates_count = len(updated_values)
        value_or_values = "values" if updates_count > 1 else "value"
        title = f"Updated {value_or_values} in {updated_file_name}"
        description = f"Updated {updates_count} {value_or_values} in `{updated_file_name}`:\n"
        description += f"```yaml\n{yaml_dump(updated_values)}\n```\n"
        return title, description

    def __commit(self, git_repo: GitRepo, message: str) -> None:
        commit_hash = git_repo.commit(self.__args.git_user, self.__args.git_email, message)
        if commit_hash:
            self.__commit_hashes.append(commit_hash)

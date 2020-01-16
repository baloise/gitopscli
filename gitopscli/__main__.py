import argparse
import sys
import uuid
from .git_util import GitUtil
from .yaml_util import yaml_load, update_yaml_file


def main():
    parser = argparse.ArgumentParser(description="GitOps CLI")
    subparsers = parser.add_subparsers(title="commands")

    deploy_p = subparsers.add_parser("deploy", help="Trigger a new deployment by changing YAML values")
    deploy_p.set_defaults(command="deploy")
    deploy_p.add_argument("-r", "--repo", help="the repository URL", required=True)
    deploy_p.add_argument("-f", "--file", help="the YAML file path", required=True)
    deploy_p.add_argument(
        "-v", "--values", help="YAML string with key-value pairs to write", type=yaml_load, required=True,
    )
    deploy_p.add_argument("-b", "--branch", help="the branch to create (default: random UUID)")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "deploy":
        deploy(args.repo, args.file, args.values, args.branch)


def deploy(repo, file_path, values, branch_name):
    if not branch_name:
        branch_name = str(uuid.uuid4())

    git = GitUtil(repo, branch_name)
    full_file_path = git.get_full_file_path(file_path)

    for key in values:
        value = values[key]
        update_yaml_file(full_file_path, key, value)
        git.commit(f"changed '{key}' to '{value}'")

    git.push()


if __name__ == "__main__":
    main()

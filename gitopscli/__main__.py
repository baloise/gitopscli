import argparse
import sys
import yaml


def main():
    parser = argparse.ArgumentParser(description="GitOps CLI")
    subparsers = parser.add_subparsers(title="commands")

    deploy_p = subparsers.add_parser("deploy", help="Trigger a new deployment by changing YAML values")
    deploy_p.set_defaults(command="deploy")
    deploy_p.add_argument("-r", "--repo", help="the repository URL", required=True)
    deploy_p.add_argument("-f", "--file", help="the YAML file path", required=True)
    deploy_p.add_argument(
        "-v", "--values", help="YAML string with key-value pairs to write", type=yaml.safe_load, required=True,
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    print(args)


if __name__ == "__main__":
    main()

import logging
import sys

from gitopscli.cliparser import parse_args
from gitopscli.commands import CommandFactory
from gitopscli.gitops_exception import GitOpsException


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-2s %(funcName)s: %(message)s")
    verbose, args = parse_args(sys.argv[1:])
    command = CommandFactory.create(args)
    try:
        command.execute()
    except GitOpsException as ex:
        if verbose:
            logging.exception(ex)  # noqa: TRY401
        else:
            logging.error(ex)  # noqa: TRY400
            logging.error("Provide verbose flag '-v' for more error details...")  # noqa: TRY400
        sys.exit(1)


if __name__ == "__main__":
    main()

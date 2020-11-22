from gitopscli.cli import DeletePreviewArgs, DeletePrPreviewArgs
from .delete_preview import delete_preview_command


def delete_pr_preview_command(args: DeletePrPreviewArgs) -> None:
    delete_preview_command(
        DeletePreviewArgs(
            username=args.username,
            password=args.password,
            git_user=args.git_user,
            git_email=args.git_email,
            organisation=args.organisation,
            repository_name=args.repository_name,
            git_provider=args.git_provider,
            git_provider_url=args.git_provider_url,
            preview_id=args.branch,  # use branch as preview id
            expect_preview_exists=args.expect_preview_exists,
        )
    )

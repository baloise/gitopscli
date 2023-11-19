import shutil
import uuid
from pathlib import Path


def create_tmp_dir() -> str:
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"  # noqa: S108
    Path(tmp_dir).mkdir(parents=True)
    return tmp_dir


def delete_tmp_dir(tmp_dir: str) -> None:
    shutil.rmtree(tmp_dir, ignore_errors=True)

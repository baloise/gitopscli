import uuid
import os
import shutil


def create_tmp_dir():
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)
    return tmp_dir


def delete_tmp_dir(tmp_dir):
    shutil.rmtree(tmp_dir, ignore_errors=True)

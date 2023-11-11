import os
import shutil
import unittest
import uuid
from pathlib import Path

from gitopscli.io_api.tmp_dir import create_tmp_dir, delete_tmp_dir


class TmpDirTest(unittest.TestCase):
    tmp_dir = None

    def tearDown(self):
        if self.tmp_dir:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_create_tmp_dir(self):
        self.tmp_dir = create_tmp_dir()
        self.assertRegex(
            self.tmp_dir, r"^/tmp/gitopscli/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        self.assertTrue(os.path.isdir(self.tmp_dir))

    def test_delete_tmp_dir(self):
        self.tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
        Path(self.tmp_dir).mkdir(parents=True)
        self.assertTrue(os.path.isdir(self.tmp_dir))
        delete_tmp_dir(self.tmp_dir)
        self.assertFalse(os.path.isdir(self.tmp_dir))
        self.tmp_dir = None

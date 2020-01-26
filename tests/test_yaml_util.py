import os
import shutil
import unittest
import uuid

from gitopscli.yaml_util import yaml_load, update_yaml_file


class YamlUtilTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = f"/tmp/gitopscli-test-{uuid.uuid4()}"
        os.makedirs(cls.tmp_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_yaml_load(self):
        self.assertEqual(yaml_load("{answer: '42'}"), {"answer": "42"})
        self.assertEqual(yaml_load("{answer: 42}"), {"answer": 42})

    def test_update_yaml_file(self):
        test_file = f"{self.tmp_dir}/{uuid.uuid4()}.yml"
        with open(test_file, "w+") as stream:
            stream.write("a: # comment\n")
            stream.write("# comment\n")
            stream.write("  b:\n")
            stream.write("    d: 1 # comment\n")
            stream.write("    c: 2 # comment\n")
            stream.write("list:\n")
            stream.write("  - listentry1\n")
            stream.write("  - listentry2\n")

        update_yaml_file(test_file, "a.b.c", "2")

        with open(test_file, "r+") as stream:
            self.assertEqual(stream.readline(), "a: # comment\n")
            self.assertEqual(stream.readline(), "# comment\n")
            self.assertEqual(stream.readline(), "  b:\n")
            self.assertEqual(stream.readline(), "    d: 1 # comment\n")
            self.assertEqual(stream.readline(), "    c: '2' # comment\n")
            self.assertEqual(stream.readline(), "list:\n")
            self.assertEqual(stream.readline(), "  - listentry1\n")
            self.assertEqual(stream.readline(), "  - listentry2\n")
            self.assertEqual(stream.readline(), "")

        update_yaml_file(test_file, "a.x", "foo")

        with open(test_file, "r+") as stream:
            self.assertEqual(stream.readline(), "a: # comment\n")
            self.assertEqual(stream.readline(), "# comment\n")
            self.assertEqual(stream.readline(), "  b:\n")
            self.assertEqual(stream.readline(), "    d: 1 # comment\n")
            self.assertEqual(stream.readline(), "    c: '2' # comment\n")
            self.assertEqual(stream.readline(), "  x: foo\n")
            self.assertEqual(stream.readline(), "list:\n")
            self.assertEqual(stream.readline(), "  - listentry1\n")
            self.assertEqual(stream.readline(), "  - listentry2\n")
            self.assertEqual(stream.readline(), "")

        update_yaml_file(test_file, "a.x.z", "foo_z")
        update_yaml_file(test_file, "a.x.y", "foo_y")
        update_yaml_file(test_file, "a.x.y.z", "foo_y_z")

        with open(test_file, "r+") as stream:
            self.assertEqual(stream.readline(), "a: # comment\n")
            self.assertEqual(stream.readline(), "# comment\n")
            self.assertEqual(stream.readline(), "  b:\n")
            self.assertEqual(stream.readline(), "    d: 1 # comment\n")
            self.assertEqual(stream.readline(), "    c: '2' # comment\n")
            self.assertEqual(stream.readline(), "  x:\n")
            self.assertEqual(stream.readline(), "    z: foo_z\n")
            self.assertEqual(stream.readline(), "    y:\n")
            self.assertEqual(stream.readline(), "      z: foo_y_z\n")
            self.assertEqual(stream.readline(), "list:\n")
            self.assertEqual(stream.readline(), "  - listentry1\n")
            self.assertEqual(stream.readline(), "  - listentry2\n")
            self.assertEqual(stream.readline(), "")

        update_yaml_file(test_file, "list", "newlistentry")

        with open(test_file, "r+") as stream:
            self.assertEqual(stream.readline(), "a: # comment\n")
            self.assertEqual(stream.readline(), "# comment\n")
            self.assertEqual(stream.readline(), "  b:\n")
            self.assertEqual(stream.readline(), "    d: 1 # comment\n")
            self.assertEqual(stream.readline(), "    c: '2' # comment\n")
            self.assertEqual(stream.readline(), "  x:\n")
            self.assertEqual(stream.readline(), "    z: foo_z\n")
            self.assertEqual(stream.readline(), "    y:\n")
            self.assertEqual(stream.readline(), "      z: foo_y_z\n")
            self.assertEqual(stream.readline(), "list:\n")
            self.assertEqual(stream.readline(), "  - listentry1\n")
            self.assertEqual(stream.readline(), "  - listentry2\n")
            self.assertEqual(stream.readline(), "  - newlistentry\n")
            self.assertEqual(stream.readline(), "")

import os
import shutil
import unittest
import uuid

from gitopscli.yaml_util import yaml_load, update_yaml_file, merge_yaml_element


class YamlUtilTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = f"/tmp/gitopscli-test-{uuid.uuid4()}"
        os.makedirs(cls.tmp_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def _create_file(self, content):
        path = f"{self.tmp_dir}/{uuid.uuid4()}"
        with open(path, "w+") as stream:
            stream.write(content)
        return path

    def _read_file(self, path):
        with open(path, "r") as stream:
            return stream.read()

    def test_yaml_load(self):
        self.assertEqual(yaml_load("{answer: '42'}"), {"answer": "42"})
        self.assertEqual(yaml_load("{answer: 42}"), {"answer": 42})

    def test_update_yaml_file(self):
        test_file = self._create_file(
            """\
a: # comment
# comment
  b:
    d: 1 # comment
    c: 2 # comment"""
        )

        update_yaml_file(test_file, "a.b.c", "2")

        expected = """\
a: # comment
# comment
  b:
    d: 1 # comment
    c: '2' # comment
"""
        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

        update_yaml_file(test_file, "a.x", "foo")

        expected = """\
a: # comment
# comment
  b:
    d: 1 # comment
    c: '2' # comment
  x: foo
"""
        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

        update_yaml_file(test_file, "a.x.z", "foo_z")
        update_yaml_file(test_file, "a.x.y", "foo_y")
        update_yaml_file(test_file, "a.x.y.z", "foo_y_z")

        expected = """\
a: # comment
# comment
  b:
    d: 1 # comment
    c: '2' # comment
  x:
    z: foo_z
    y:
      z: foo_y_z
"""
        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

    def test_merge_yaml_element(self):
        test_file = self._create_file(
            """\
# Kept comment
applications:
  app1: # Lost comment
  app2:
    key: value # Lost comment
"""
        )

        value = {"app2": {"key2": "value"}, "app3": None}
        merge_yaml_element(test_file, "applications", value, True)

        expected = """\
# Kept comment
applications:
  app2:
    key: value
    key2: value
  app3:
"""
        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

    def test_merge_yaml_element_root_dir(self):
        test_file = self._create_file(
            """\
applications:
  app1: # Lost comment
  app2: # Lost comment
    key: value # Lost comment
"""
        )

        value = {"applications": {"app2": {"key2": "value"}, "app3": None}}
        merge_yaml_element(test_file, ".", value, True)

        expected = """\
applications:
  app1:
  app2:
    key2: value
  app3:
"""
        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

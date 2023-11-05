import os
import shutil
import unittest
import uuid

import pytest

from gitopscli.io_api.yaml_util import (
    YAMLException,
    merge_yaml_element,
    update_yaml_file,
    yaml_dump,
    yaml_file_dump,
    yaml_file_load,
    yaml_load,
)


class YamlUtilTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = f"/tmp/gitopscli-test-{uuid.uuid4()}"
        os.makedirs(cls.tmp_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def _create_tmp_file_path(self):
        return f"{self.tmp_dir}/{uuid.uuid4()}"

    def _create_file(self, content):
        path = self._create_tmp_file_path()
        with open(path, "w") as stream:
            stream.write(content)
        return path

    def _read_file(self, path):
        with open(path, "r") as stream:
            return stream.read()

    def test_yaml_file_load(self):
        path = self._create_file("answer: #comment\n  is: '42'\n")
        self.assertEqual(yaml_file_load(path), {"answer": {"is": "42"}})

    def test_yaml_file_load_file_not_found(self):
        try:
            yaml_file_load("unknown")
            self.fail()
        except FileNotFoundError:
            pass

    def test_yaml_file_load_yaml_exception(self):
        path = self._create_file("{ INVALID YAML")
        try:
            yaml_file_load(path)
            self.fail()
        except YAMLException as ex:
            self.assertEqual(f"Error parsing YAML file: {path}", str(ex))

    def test_yaml_file_dump(self):
        path = self._create_tmp_file_path()
        yaml_file_dump({"answer": {"is": "42"}}, path)
        yaml_content = self._read_file(path)
        self.assertEqual(yaml_content, "answer:\n  is: '42'\n")

    def test_yaml_file_dump_unknown_directory(self):
        try:
            yaml_file_dump({"answer": {"is": "42"}}, "/unknown-dir/foo")
            self.fail()
        except FileNotFoundError:
            pass

    def test_yaml_file_load_and_dump_roundtrip(self):
        input_content = "answer: #comment\n  is: '42'\n"  # comment should be preserved
        input_path = self._create_file(input_content)
        yaml = yaml_file_load(input_path)
        output_path = self._create_tmp_file_path()
        yaml_file_dump(yaml, output_path)
        output_content = self._read_file(output_path)
        self.assertEqual(output_content, input_content)

    def test_yaml_load(self):
        self.assertEqual(yaml_load("{answer: '42'}"), {"answer": "42"})
        self.assertEqual(yaml_load("{answer: 42}"), {"answer": 42})
        self.assertEqual(yaml_load("answer: 42"), {"answer": 42})

    def test_yaml_load_yaml_exception(self):
        try:
            yaml_load("{ INVALID YAML")
            self.fail()
        except YAMLException as ex:
            self.assertEqual("Error parsing YAML string '{ INVALID YAML'", str(ex))

    def test_yaml_dump(self):
        self.assertEqual(yaml_dump({"answer": "42"}), "answer: '42'")
        self.assertEqual(yaml_dump({"answer": 42}), "answer: 42")
        self.assertEqual(
            yaml_dump({"answer": "42", "universe": ["and", "everything"]}),
            """\
answer: '42'
universe:
- and
- everything""",
        )

    def test_update_yaml_file(self):
        test_file = self._create_file(
            """\
a: # comment 1
# comment 2
  b:
    d: 1 # comment 3
    c: 2 # comment 4
    e: "expect quotes are preserved"
  e:
  - f: 3 # comment 5
    g: 4 # comment 6
  - [hello, world] # comment 7
  - foo: # comment 8
      bar # comment 9
  - list: # comment 10
    - key: k1 # comment 11
      value: v1 # comment 12
    - key: k2 # comment 13
      value: v2 # comment 14
    - {key: k3+4, value: v3} # comment 15
    - key: k3+4 # comment 16
      value: v4 # comment 17"""
        )

        self.assertTrue(update_yaml_file(test_file, "a.b.c", "2"))
        self.assertFalse(update_yaml_file(test_file, "a.b.c", "2"))  # already updated

        self.assertTrue(update_yaml_file(test_file, "a.e.[0].g", 42))
        self.assertFalse(update_yaml_file(test_file, "a.e.[0].g", 42))  # already updated

        self.assertTrue(update_yaml_file(test_file, "a.e.[1].[1]", "tester"))
        self.assertFalse(update_yaml_file(test_file, "a.e.[1].[1]", "tester"))  # already updated

        self.assertTrue(update_yaml_file(test_file, "a.e.[2]", "replaced object"))
        self.assertFalse(update_yaml_file(test_file, "a.e.[2]", "replaced object"))  # already updated

        self.assertTrue(update_yaml_file(test_file, "a.e.[*].list[?key=='k3+4'].value", "replaced v3 and v4"))
        self.assertFalse(
            update_yaml_file(test_file, "a.e.[*].list[?key=='k3+4'].value", "replaced v3 and v4")
        )  # already updated

        expected = """\
a: # comment 1
# comment 2
  b:
    d: 1 # comment 3
    c: '2' # comment 4
    e: "expect quotes are preserved"
  e:
  - f: 3 # comment 5
    g: 42 # comment 6
  - [hello, tester] # comment 7
  - replaced object
  - list: # comment 10
    - key: k1 # comment 11
      value: v1 # comment 12
    - key: k2 # comment 13
      value: v2 # comment 14
    - {key: k3+4, value: replaced v3 and v4} # comment 15
    - key: k3+4 # comment 16
      value: replaced v3 and v4 # comment 17
"""
        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "x.y", "foo")
        self.assertEqual("\"Key 'x.y' not found in YAML!\"", str(ex.value))

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "[42].y", "foo")
        self.assertEqual("\"Key '[42].y' not found in YAML!\"", str(ex.value))

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "a.x", "foo")
        self.assertEqual("\"Key 'a.x' not found in YAML!\"", str(ex.value))

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "a.[42]", "foo")
        self.assertEqual("\"Key 'a.[42]' not found in YAML!\"", str(ex.value))

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "a.e.[100]", "foo")
        self.assertEqual("\"Key 'a.e.[100]' not found in YAML!\"", str(ex.value))

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "a.e.[*].list[?key=='foo'].value", "foo")
        self.assertEqual("\"Key 'a.e.[*].list[?key=='foo'].value' not found in YAML!\"", str(ex.value))

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "a.e.[2].[2]", "foo")
        self.assertEqual(
            "\"Key 'a.e.[2].[2]' cannot be updated: 'str' object does not support item assignment!\"", str(ex.value)
        )

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "invalid JSONPath", "foo")
        self.assertEqual(
            "\"Key 'invalid JSONPath' is invalid JSONPath expression: Parse error at 1:8 near token JSONPath (ID)!\"",
            str(ex.value),
        )

        with pytest.raises(KeyError) as ex:
            update_yaml_file(test_file, "", "foo")
        self.assertEqual("'Empty key!'", str(ex.value))

        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

    def test_update_yaml_file_not_found_error(self):
        try:
            update_yaml_file("/some-unknown-dir/some-random-unknown-file", "a.b", "foo")
            self.fail()
        except FileNotFoundError:
            pass

    def test_update_yaml_file_is_a_directory_error(self):
        try:
            update_yaml_file("/tmp", "a.b", "foo")
            self.fail()
        except IsADirectoryError:
            pass

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
        merge_yaml_element(test_file, "applications", value)

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

    def test_merge_yaml_element_create(self):
        test_file = self._create_file(
            """\
# Kept comment
applications: null
"""
        )

        value = {"app2": {"key2": "value"}, "app3": None}
        merge_yaml_element(test_file, "applications", value)

        expected = """\
# Kept comment
applications:
  app2:
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
        merge_yaml_element(test_file, ".", value)

        expected = """\
applications:
  app1:
  app2:
    key2: value
  app3:
"""
        actual = self._read_file(test_file)
        self.assertEqual(expected, actual)

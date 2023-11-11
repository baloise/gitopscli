import locale
from io import StringIO
from pathlib import Path
from typing import Any

from jsonpath_ng.exceptions import JSONPathError
from jsonpath_ng.ext import parse
from ruamel.yaml import YAML, YAMLError

YAML_INSTANCE = YAML()
YAML_INSTANCE.preserve_quotes = True


class YAMLException(Exception):  # noqa: N818
    pass


def yaml_file_load(file_path: str) -> Any:
    with Path(file_path).open(encoding=locale.getpreferredencoding(do_setlocale=False)) as stream:
        try:
            return YAML_INSTANCE.load(stream)
        except YAMLError as ex:
            raise YAMLException(f"Error parsing YAML file: {file_path}") from ex


def yaml_file_dump(yaml: Any, file_path: str) -> None:
    with Path(file_path).open("w+", encoding=locale.getpreferredencoding(do_setlocale=False)) as stream:
        YAML_INSTANCE.dump(yaml, stream)


def yaml_load(yaml_str: str) -> Any:
    try:
        return YAML_INSTANCE.load(yaml_str)
    except YAMLError as ex:
        raise YAMLException(f"Error parsing YAML string '{yaml_str}'") from ex


def yaml_dump(yaml: Any) -> str:
    stream = StringIO()
    YAML_INSTANCE.dump(yaml, stream)
    return stream.getvalue().rstrip()


def update_yaml_file(file_path: str, key: str, value: Any) -> bool:
    if not key:
        raise KeyError("Empty key!")
    content = yaml_file_load(file_path)
    try:
        jsonpath_expr = parse(key)
    except JSONPathError as ex:
        raise KeyError(f"Key '{key}' is invalid JSONPath expression: {ex}!") from ex
    matches = jsonpath_expr.find(content)
    if not matches:
        raise KeyError(f"Key '{key}' not found in YAML!")
    if all(match.value == value for match in matches):
        return False  # nothing to update
    try:
        jsonpath_expr.update(content, value)
    except TypeError as ex:
        raise KeyError(f"Key '{key}' cannot be updated: {ex}!") from ex
    yaml_file_dump(content, file_path)
    return True


def merge_yaml_element(file_path: str, element_path: str, desired_value: Any) -> None:
    yaml_file_content = yaml_file_load(file_path)
    work_path = yaml_file_content

    if element_path != ".":
        path_list = element_path.split(".")
        for key in path_list:
            if work_path[key] is None:
                work_path[key] = {}
            work_path = work_path[key]

    for key, value in desired_value.items():
        tmp_value = value
        if key in work_path and work_path[key] is not None:
            tmp_value = {**work_path[key], **tmp_value}
        work_path[key] = tmp_value

    # delete missing key:
    current = work_path.copy().items()
    for key, _ in current:
        if key not in desired_value:
            del work_path[key]

    yaml_file_dump(yaml_file_content, file_path)

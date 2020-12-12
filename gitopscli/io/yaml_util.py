import re
from io import StringIO
from typing import Any
from ruamel.yaml import YAML, YAMLError


_ARRAY_KEY_SEGMENT_PATTERN = re.compile(r"\[(\d+)\]")


class YAMLException(Exception):
    pass


def yaml_file_load(file_path: str) -> Any:
    with open(file_path, "r") as stream:
        try:
            return YAML().load(stream)
        except YAMLError as ex:
            raise YAMLException(f"Error parsing YAML file: {file_path}") from ex


def yaml_file_dump(yaml: Any, file_path: str) -> None:
    with open(file_path, "w+") as stream:
        YAML().dump(yaml, stream)


def yaml_load(yaml_str: str) -> Any:
    try:
        return YAML().load(yaml_str)
    except YAMLError as ex:
        raise YAMLException(f"Error parsing YAML string '{yaml_str}'") from ex


def yaml_dump(yaml: Any) -> str:
    stream = StringIO()
    YAML().dump(yaml, stream)
    return stream.getvalue().rstrip()


def update_yaml_file(file_path: str, key: str, value: Any) -> bool:
    content = yaml_file_load(file_path)

    key_segments = key.split(".") if key else []
    current_key_segments = []
    parent_item = content
    for current_key_segment in key_segments:
        current_key_segments.append(current_key_segment)
        current_key = ".".join(current_key_segments)
        is_array = _ARRAY_KEY_SEGMENT_PATTERN.match(current_key_segment)
        if is_array:
            current_array_index = int(is_array.group(1))
            if not isinstance(parent_item, list) or current_array_index >= len(parent_item):
                raise KeyError(f"Key '{current_key}' not found in YAML!")
        else:
            if not isinstance(parent_item, dict) or current_key_segment not in parent_item:
                raise KeyError(f"Key '{current_key}' not found in YAML!")
        if current_key == key:
            if parent_item[current_array_index if is_array else current_key_segment] == value:
                return False  # nothing to update
            parent_item[current_array_index if is_array else current_key_segment] = value
            yaml_file_dump(content, file_path)
            return True
        parent_item = parent_item[current_array_index if is_array else current_key_segment]
    raise KeyError(f"Empty key!")


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
        if key in work_path:
            if work_path[key] is not None:
                value = {**work_path[key], **value}
        work_path[key] = value

    # delete missing key:
    current = work_path.copy().items()
    for key, value in current:
        if key not in desired_value:
            del work_path[key]

    yaml_file_dump(yaml_file_content, file_path)

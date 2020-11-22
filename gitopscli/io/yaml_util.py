import re
from io import StringIO
from typing import Any
from ruamel.yaml import YAML

ARRAY_KEY_SEGMENT_PATTERN = re.compile(r"\[(\d+)\]")


def yaml_load(yaml_str: str) -> Any:
    return YAML().load(yaml_str)


def yaml_dump(yaml: Any) -> str:
    stream = StringIO()
    YAML().dump(yaml, stream)
    return stream.getvalue().rstrip()


def update_yaml_file(file_path: str, key: str, value: Any) -> bool:
    yaml = YAML()
    with open(file_path, "r") as stream:
        content = yaml.load(stream)

    key_segments = key.split(".")
    current_key_segments = []
    parent_item = content
    for current_key_segment in key_segments:
        current_key_segments.append(current_key_segment)
        current_key = ".".join(current_key_segments)
        is_array = ARRAY_KEY_SEGMENT_PATTERN.match(current_key_segment)
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
            with open(file_path, "w+") as stream:
                yaml.dump(content, stream)
            return True
        parent_item = parent_item[current_array_index if is_array else current_key_segment]
    raise KeyError(f"Empty key!")


def merge_yaml_element(file_path: str, element_path: str, desired_value: Any) -> None:
    yaml = YAML()
    with open(file_path, "r") as stream:
        yaml_file_content = yaml.load(stream)
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

    with open(file_path, "w+") as stream:
        yaml.dump(yaml_file_content, stream)

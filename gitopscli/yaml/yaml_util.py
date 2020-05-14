import re
from ruamel.yaml import YAML

ARRAY_KEY_SEGMENT_PATTERN = re.compile(r"\[(\d+)\]")


def yaml_load(doc):
    return YAML().load(doc)


def yaml_dump(data):
    class FakeStream:
        _byte_strings = []

        def write(self, byte_string):
            self._byte_strings.append(byte_string)

        def get_string(self):
            return b"".join(self._byte_strings).decode("utf-8").rstrip()

    stream = FakeStream()
    YAML().dump(data, stream)
    return stream.get_string()


def update_yaml_file(file_path, key, value):
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
            current_key_segment = int(is_array.group(1))
            if not isinstance(parent_item, list) or current_key_segment >= len(parent_item):
                raise KeyError(f"Key '{current_key}' not found in YAML!")
        else:
            if not isinstance(parent_item, dict) or current_key_segment not in parent_item:
                raise KeyError(f"Key '{current_key}' not found in YAML!")
        if current_key == key:
            if parent_item[current_key_segment] == value:
                return False  # nothing to update
            parent_item[current_key_segment] = value
            with open(file_path, "w+") as stream:
                yaml.dump(content, stream)
            return True
        parent_item = parent_item[current_key_segment]
    raise KeyError(f"Empty key!")


def merge_yaml_element(file_path, element_path, desired_value, delete_missing_key=False):
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

    if delete_missing_key:
        current = work_path.copy().items()
        for key, value in current:
            if key not in desired_value:
                del work_path[key]

    with open(file_path, "w+") as stream:
        yaml.dump(yaml_file_content, stream)

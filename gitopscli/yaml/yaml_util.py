import re
from ruamel.yaml import YAML

INDEX_PATTERN = re.compile(r"\[(\d+)\]")


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

    keys, item = key.split("."), content
    leaf_idx = len(keys) - 1
    current_key_segments = []
    current_key = ""
    for i, k in enumerate(keys):
        current_key_segments.append(k)
        current_key = ".".join(current_key_segments)
        is_array = INDEX_PATTERN.match(k)
        if is_array:
            k = int(is_array.group(1))
            if not isinstance(item, list) or k >= len(item):
                raise KeyError(f"Key '{current_key}' not found in YAML!")
        else:
            if not isinstance(item, dict) or k not in item:
                raise KeyError(f"Key '{current_key}' not found in YAML!")
        if i == leaf_idx:
            if item[k] == value:
                return False  # nothing to update
            item[k] = value
            break
        item = item[k]

    with open(file_path, "w+") as stream:
        yaml.dump(content, stream)
    return True


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

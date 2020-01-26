import pprint

from ruamel.yaml import YAML


def yaml_load(doc):
    return YAML().load(doc)


def update_yaml_file(file_path, key, value):
    yaml = YAML()
    with open(file_path, "r") as stream:
        content = yaml.load(stream)

    keys, obj = key.split("."), content
    for k in keys[:-1]:
        if k not in obj or not isinstance(obj[k], dict):
            obj[k] = dict()
        obj = obj[k]
    obj[keys[-1]] = value

    with open(file_path, "w+") as stream:
        yaml.dump(content, stream)


def merge_yaml_element(file_path, element_path, desired_value, delete_missing_key=False):
    yaml = YAML()
    with open(file_path, "r") as stream:
        yaml_file_content = yaml.load(stream)
    pprint.pprint(yaml_file_content)
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

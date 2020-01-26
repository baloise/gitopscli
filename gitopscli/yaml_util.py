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


def merge_yaml_element(file_path, element_path, value, delete_missing_key=False):
    yaml = YAML()
    with open(file_path, "r") as stream:
        yaml_file_content = yaml.load(stream)
    pprint.pprint(yaml_file_content)
    work_path = yaml_file_content

    if element_path != ".":
        path_list = element_path.split(".")
        for k in path_list:
            if work_path[k] is None:
                work_path[k] = {}
            work_path = work_path[k]

    for k, v in value.items():
        if k in work_path:
            if work_path[k] is not None:
                v = {**work_path[k], **v}
        work_path[k] = v

    if delete_missing_key:
        current = work_path.copy().items()
        for k, v in current:
            if k not in value:
                del work_path[k]

    with open(file_path, "w+") as stream:
        yaml.dump(yaml_file_content, stream)

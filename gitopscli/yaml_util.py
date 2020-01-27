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

    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(file_path, "w+") as stream:
        yaml.dump(content, stream)

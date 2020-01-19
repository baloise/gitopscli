from ruamel.yaml import YAML


def yaml_load(doc):
    return YAML().load(doc)


def update_yaml_file(file_path, key, value):
    yaml = YAML()
    content = yaml.load(file_path)

    keys, obj = key.split("."), content
    for k in keys[:-1]:
        obj = obj[k]
    obj[keys[-1]] = value

    with open(file_path, "w+") as output:
        yaml.dump(content, output)

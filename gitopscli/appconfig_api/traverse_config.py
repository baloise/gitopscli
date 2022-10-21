def traverse_config(data, configver):
    path = configver[1]
    lookup = data
    for key in path:
        lookup = lookup[key]
    return lookup

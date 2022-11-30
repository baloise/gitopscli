from typing import Any


def traverse_config(data: Any, configver: Any) -> Any:
    path = configver[1]
    lookup = data
    for key in path:
        lookup = lookup[key]
    return lookup

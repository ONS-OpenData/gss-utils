from typing import Dict, TypeVar, List, Callable, Optional


def override(record: Dict, overrides: Dict):
    """
    Recursively adds overrides to record. Overwrites existing fields where conflicts arise.
    """
    for key in overrides.keys():
        if key not in record:
            record[key] = overrides[key]
        else:
            existing_value = record[key]
            overwrite_value = overrides[key]
            if isinstance(existing_value, dict):
                override(existing_value, overwrite_value)
            else:
                record[key] = overwrite_value


def supplement(record: Dict, values: Dict):
    """
    Recursively adds values to record without overwriting existing fields.
    """
    for key in values.keys():
        if key not in record:
            record[key] = values[key]
        else:
            existing_value = record[key]
            supplemental_value = values[key]
            if isinstance(existing_value, dict):
                supplement(existing_value, supplemental_value)


T = TypeVar("T")


def find(xs: List[T], predicate: Callable[[T], bool]) -> Optional[T]:
    for item in xs:
        if predicate(item):
            return item

    return None


def node_has_type(node: Dict, type_to_find: str) -> bool:
    if "@type" in node:
        t = node["@type"]
        return (isinstance(t, list) and find(t, lambda x: x == type_to_find)) or (
                isinstance(t, str) and t == type_to_find)
    return False

from typing import Dict, List
import json


def assert_properties_unset(metadata: Dict, must_not_be_set: Dict):
    for (key, must_not_value) in must_not_be_set.items():
        if key in metadata:
            value = metadata[key]
            if isinstance(must_not_value, dict):
                assert_properties_unset(value, must_not_value)
            elif isinstance(must_not_value, list):
                raise Exception("Not configured to compare lists.")
            else:
                # It's a primitive. Shouldn't be set!
                raise Exception(f"Found key '{key}' with value '{value}'.")


def assert_properties_set(metadata: Dict, must_be_set: Dict):
    for (key, must_value) in must_be_set.items():
        if key not in metadata:
            raise Exception(f"Key '{key}' could not be found.")

        value = metadata[key]
        if isinstance(must_value, dict):
            assert_properties_set(value, must_value)
        elif isinstance(must_value, list):
            _assert_all_items_set_in_list(value, must_value, key)
        elif value != must_value:
            raise Exception(f"Key '{key}' value is '{value}' but must be '{must_value}'.")


def _dict_item_set_in_list(must_item: Dict, values_list: List[Dict]) -> bool:
    for item in values_list:
        # noinspection PyBroadException
        try:
            assert_properties_set(item, must_item)
            return True
        except:
            pass

    return False


def _assert_all_items_set_in_list(values_list: List, must_values_list: List, key):
    for must_item in must_values_list:
        if isinstance(must_item, dict):
            if _dict_item_set_in_list(must_item, values_list):
                continue
            else:
                raise Exception(
                    f"Could not find matching item in Key '{key}' for expected item '{json.dumps(must_item)}'")
        elif must_item in values_list:
            continue
        else:
            raise Exception(
                f"Could not find matching item in Key '{key}' for expected item '{must_item}'")



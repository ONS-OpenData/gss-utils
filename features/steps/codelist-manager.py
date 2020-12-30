from behave import *
from behave.runner import Context
import json
from typing import Dict, List

from gssutils.codelistmanager.applyupdates import refactor_structure_with_updates


@given("We have a metadata file of the form")
def step_impl(context: Context):
    metadata_json: str = context.text
    context.metadata = json.loads(metadata_json)


@when("We run an automatic upgrade on the metadata file")
def step_impl(context: Context):
    refactor_structure_with_updates(context.metadata, False)


@then("The following properties are set")
def step_impl(context: Context):
    def dict_item_set_in_list(must_item: Dict, values_list: List[Dict]) -> bool:
        for item in values_list:
            # noinspection PyBroadException
            try:
                assert_properties_set(item, must_item)
                return True
            except:
                pass

        return False

    def assert_all_items_set_in_list(values_list: List, must_values_list: List, key):
        for must_item in must_values_list:
            if isinstance(must_item, dict):
                if dict_item_set_in_list(must_item, values_list):
                    continue
                else:
                    raise Exception(
                        f"Could not find matching item in Key '{key}' for expected item '{json.dumps(must_item)}'")
            elif must_item in values_list:
                continue
            else:
                raise Exception(
                    f"Could not find matching item in Key '{key}' for expected item '{must_item}'")

    def assert_properties_set(metadata: Dict, must_be_set: Dict):
        for (key, must_value) in must_be_set.items():
            if key not in metadata:
                raise Exception(f"Key '{key}' could not be found.")

            value = metadata[key]
            if isinstance(must_value, dict):
                assert_properties_set(value, must_value)
            elif isinstance(must_value, list):
                assert_all_items_set_in_list(value, must_value, key)
            elif value != must_value:
                raise Exception(f"Key '{key}' value is '{value}' but must be '{must_value}'.")

    properties_set_json: str = context.text
    properties_set: Dict = json.loads(properties_set_json)

    assert_properties_set(context.metadata, properties_set)


@then("The following properties are not set")
def step_impl(context: Context):
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

    properties_unset_json: str = context.text
    properties_unset: Dict = json.loads(properties_unset_json)

    assert_properties_unset(context.metadata, properties_unset)

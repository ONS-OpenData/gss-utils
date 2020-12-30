from behave import *
from behave.runner import Context
import json
from typing import Dict

from gssutils.codelistmanager.applyupdates import refactor_structure_with_updates
from gssutils.codelistmanager.createnew import generate_csvw_metadata, _map_str_to_code_list_level
from gssutils.utils import pathify
from dictcomparisonutils import assert_properties_set, assert_properties_unset


@given("We have a metadata file of the form")
def step_impl(context: Context):
    metadata_json: str = context.text
    context.metadata = json.loads(metadata_json)


@when("We run an automatic upgrade on the metadata file")
def step_impl(context: Context):
    refactor_structure_with_updates(context.metadata, False)


@then("The following properties are set")
def step_impl(context: Context):
    properties_set_json: str = context.text
    properties_set: Dict = json.loads(properties_set_json)

    assert_properties_set(context.metadata, properties_set)


@then("The following properties are not set")
def step_impl(context: Context):
    properties_unset_json: str = context.text
    properties_unset: Dict = json.loads(properties_unset_json)

    assert_properties_unset(context.metadata, properties_unset)


@given("We have a CSV file named \"{csv_file_name}\" with headers")
def step_impl(context: Context, csv_file_name: str):
    headers: str = context.text
    context.headers = [h.strip() for h in headers.split(',')]
    context.csv_file_name = csv_file_name
    context.maybe_info_json_metadata = None


@given("The code list is in the \"{family_name}\" family")
def step_impl(context: Context, family_name: str):
    context.maybe_family_name = family_name


@given("We have an info json config of the form")
def step_impl(context: Context):
    context.maybe_info_json_metadata = json.loads(context.text)


@when("We generate a CSVW metadata file at the {level} level")
def step_impl(context: Context, level: str):
    """
    We accept `(G)lobal`, `(f)amily` and `(d)ataset` as levels.
    """
    code_list_level = _map_str_to_code_list_level(level[0])
    context.metadata = generate_csvw_metadata(context.headers, context.csv_file_name, code_list_level,
                                              context.maybe_info_json_metadata,
                                              lambda: pathify(context.maybe_family_name))
import os
import json
import logging

from pathlib import Path

from gssutils.transform.codelists import get_codelist_schema
from gssutils import *

def get_fixture(file_name):
    """Helper to get specific files out of the fixtures dir"""
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    fixture_file_path = Path(feature_path, "fixtures", file_name)
    return fixture_file_path

@given('I want to create datacubes from the seed "{seed_name}"')
def step_impl(context, seed_name):
    context.cubes = Cubes(get_fixture(seed_name))

@step('I specifiy a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}"')
def step_impl(context, cube_name, csv_data, seed_name):
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.read_csv(get_fixture(csv_data))
    context.cubes.add_cube(scraper, df, cube_name)

@step('the datacube outputs can be created')
def stemp_impl(context):
    context.cubes.output_all()

@then('the output metadata references the correct number of namespaces')
def stemp_impl(context):

    # For pipeleines delivering a single cube, a slightly different trig is used
    # We're basically checking the first (single cubes) or the last (multi cubes)
    if len(context.cubes.cubes) == 1:
        trig = context.cubes.cubes[0].singleton_trig
        namespaces = len([x for x in trig.decode().split("\n") if x.startswith("@prefix ns")]) - 2
    else:
        trig = context.cubes.cubes[-1].multi_trig
        namespaces = len([x for x in trig.decode().split("\n") if x.startswith("@prefix ns")])

    expected_num_of_namespaces = len(context.cubes.cubes)
    assert namespaces == len(context.cubes.cubes), \
        "Datacube has the wrong number of namespaces, got {}, expected {}." \
            .format(namespaces, expected_num_of_namespaces)

@then('the schema for codelist "{codelist_name}" is created which matches "{correct_schema}"')
def stemp_impl(context, codelist_name, correct_schema):
    created_schema_as_dict = get_codelist_schema(codelist_name, context.cubes.base_url, 
                                    context.cubes.cubes[0].title)

    # Get the "correct" schema from the fixtures
    with open(get_fixture(correct_schema), "r") as f:
        correct_schema_as_dict = json.load(f)

    # compare
    assert created_schema_as_dict == correct_schema_as_dict, "{}\n\n Above schema does not " \
            "match the expected schema for: '{}', specified in {}.".format(json.dumps(created_schema_as_dict, indent=2),
                codelist_name, "features/fixtures/{}".format(correct_schema))

@then('the csv-w schema for "{cube_name}" matches "{correct_schema}"')
def stemp_impl(context, cube_name, correct_schema):
    
    # check we actually have the requested cube
    matched_cubes = [x for x in context.cubes.cubes if x.title == cube_name]
    assert len(matched_cubes) == 1, f"Unable to find datacube {cube_name}"
    
    this_cube = matched_cubes[0]

    # Set the "obs file" as a test csv in the fixtures
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    obs_fixture_path = Path(feature_path, "fixtures")
    schemaMapObj = this_cube._populate_csvw_mapping(obs_fixture_path, 
                        pathify(cube_name), context.cubes.info)
    
    # Create the schema
    created_schema_as_dict = schemaMapObj._as_plain_obj(schemaMapObj._as_csvw_object())

    # Get the "correct" schema from the fixtures
    with open(get_fixture(correct_schema), "r") as f:
        correct_schema_as_dict = json.load(f)

    # compare
    assert created_schema_as_dict == correct_schema_as_dict, "{}\n\n Above schema does not " \
            "match the expected schema for: '{}'.".format(json.dumps(created_schema_as_dict, indent=2),
                correct_schema)


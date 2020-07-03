import os
import json

from gssutils import *
import logging

def get_fixture(file_name):
    """Helper to get specific files out of the fixtures dir"""
    feature_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    fixture_file_path = os.path.join(feature_path, "fixtures", file_name)
    return fixture_file_path

@given('I want to create datacubes from the seed "{seed_name}"')
def step_impl(context, seed_name):
    context.cubes = Cubes(get_fixture(seed_name))

@step('I specifiy a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}"')
def step_impl(context, cube_name, csv_data, seed_name):
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.DataFrame()
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

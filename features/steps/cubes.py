import os
import json

from gssutils import *

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

@then('datacube "{cube_no}" references "{expected_num_of_namespaces}" datacube namspace(s)')
def stemp_impl(context, cube_no, expected_num_of_namespaces):

    # TODO - will likely all need refactoring for mapping
    cube_no = int(cube_no)-1
    cube = context.cubes.cubes[cube_no]

    # For pipeleines delivering a single cube, a slightly different trig is used
    trig = None
    if len(context.cubes.cubes) == 1:
        trig = cube.singleton_trig
    else:
        trig = cube.multi_trig

    # For multiple cubes, the number of namespaces declared in the trig is relative to the number
    # of cubes proccessed (cumulatively) by a given transform script.
    # The very first cube output has a slightly different namespace declaration

    # TODO - fix cicular logic
    namespace_mod = cube.process_order - 2 if len(context.cubes.cubes) > 1 else -1
    namespaces = len([x for x in trig.decode().split("\n") if x.startswith("@prefix ns")]) \
                        - (cube.process_order - namespace_mod)

    assert namespaces == int(expected_num_of_namespaces), "Datacube {} has the wrong number of namespaces" \
                                " got {}, expected {}.".format(cube_no+1, namespaces, 
                                expected_num_of_namespaces)
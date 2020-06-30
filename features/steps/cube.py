import os
import json

from gssutils import *

@given('I create a list of datacubes for data family "{family_ref_url}"')
def step_impl(context, family_ref_url):
    context.cubes = Cubes(family_ref_url)

@step('I create a list of datacubes for "{family_ref_url}" with additional runtime metadata from "{meta_json}"')
def step_impl(context, family_ref_url, meta_json):
    feature_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    meta_path = os.path.join(feature_path, "fixtures", meta_json)
    with open(meta_path, "r") as f:
        data = json.load(f)
        context.cubes = Cubes(family_ref_url, meta_dict=data)

@step('I add a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}"')
def step_impl(context, cube_name, csv_data, seed_name):
    feature_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    seed_path = os.path.join(feature_path, "fixtures", seed_name)
    scraper = Scraper(seed=seed_path)
    df = pd.DataFrame()
    context.cubes.add_cube(scraper, df, cube_name)

@step('the datacube outputs can be created')
def stemp_impl(context):
    context.cubes.output_all(with_transform=False)

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

    # note - clearly cicular logic below but it works and its temp code we're planning
    # to remove so not gonna bother untangling it
    namespace_mod = cube.process_order - 2 if len(context.cubes.cubes) > 1 else -1
    namespaces = len([x for x in trig.decode().split("\n") if x.startswith("@prefix ns")]) \
                        - (cube.process_order - namespace_mod)

    assert namespaces == int(expected_num_of_namespaces), "Datacube {} has the wrong number of namespaces" \
                                " got {}, expected {}.".format(cube_no+1, namespaces, 
                                expected_num_of_namespaces)
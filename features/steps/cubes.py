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

@step('I specify a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}"')
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

@then('for the datacube "{cube_name}" the csv codelist "{codelist_name}" is created which matches "{correct_csv}"')
def stemp_impl(context, cube_name, codelist_name, correct_csv):
    
    # make sure we have the requested cube
    cube = [x for x in context.cubes.cubes if x.title == cube_name]
    assert len(cube) == 1, f"A cube with the name {cube_name} is not present"
    cube = cube[0]

    new_codelist_as_df = cube._build_default_codelist(cube.df[codelist_name].unique().tolist())
    correct_codelist = pd.read_csv(get_fixture(correct_csv)).fillna("")

    # we'll just concat then drop duplicates, that'll let us assert a match with a simple len
    new_df = pd.concat([correct_codelist, new_codelist_as_df]).fillna("").drop_duplicates()

    # if they don't match we'll need to munge some sensible feedback
    # TODO - better, this is hacky af
    feedback = {}
    if len(correct_codelist) != len(new_df):
        new_codelist_as_df["composite"] = ""
        for col in new_codelist_as_df.columns.values:
            new_codelist_as_df["composite"] = new_codelist_as_df["composite"] + "," + new_codelist_as_df[col]
        new_codelist_as_df["composite"] = new_codelist_as_df["composite"].str[1:]

        correct_codelist["composite"] = ""
        for col in correct_codelist.columns.values:
            correct_codelist["composite"] = correct_codelist["composite"] + "," + correct_codelist[col]
        correct_codelist["composite"] = correct_codelist["composite"].str[1:]

        unexpected = [x for x in new_codelist_as_df["composite"].unique() if x not in correct_codelist["composite"].unique()]
        missing = [x for x in correct_codelist["composite"].unique() if x not in new_codelist_as_df["composite"].unique()]
        feedback = {"unexpected rows": unexpected, "missing rows": missing}

    assert len(correct_codelist) == len(new_df), "The codelist generated for {} does not match {}" \
                " details follow: {}".format(codelist_name, f"feature/fixtues/{correct_csv}", \
                json.dumps(feedback, indent=2))

@then('for the datacube "{cube_name}" the schema for codelist "{codelist_name}" is created which matches "{correct_schema}"')
def stemp_impl(context, cube_name, codelist_name, correct_schema):

    # make sure we have the requested cube
    cube = [x for x in context.cubes.cubes if x.title == cube_name]
    assert len(cube) == 1, f"A cube with the name {cube_name} is not present"
    cube = cube[0]

    created_schema_as_dict = get_codelist_schema(codelist_name, context.cubes.base_url, cube.title)

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

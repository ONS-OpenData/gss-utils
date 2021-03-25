import json

from behave import *
from nose.tools import *
from gssutils import *


def get_fixture(file_name):
    """Helper to get specific files out of the fixtures dir"""
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    fixture_file_path = Path(feature_path, "fixtures", file_name)
    return fixture_file_path

@given('I want to create datacubes from the seed "{seed_name}"')
def step_impl(context, seed_name):
    context.cubes = Cubes(get_fixture(seed_name))

# TODO - break this down
@given('I specify a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}"')
def step_impl(context, cube_name, csv_data, seed_name):
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.read_csv(get_fixture(csv_data))
    context.cubes.add_cube(scraper, df, cube_name)

# TODO - break this waaaaay down
@given('I specify a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}" with the keyword arguments')
def step_impl(context, cube_name, csv_data, seed_name):
    kwargs = {}
    for row in context.table:
        kwargs[row[0]] = row[1]
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.read_csv(get_fixture(csv_data))
    context.cubes.add_cube(scraper, df, cube_name, **kwargs)

@then('ouputs from cube "{cube_no}" use the extension "{expected_extension}"')
def step_impl(context, cube_no, expected_extension):
    cube = context.cubes.cubes[int(cube_no)-1] # 0 indexed
    assert cube.output_extension == expected_extension, f'Expecting extension {expected_extension}, got {cube.output_extension}'

@then('the datacube outputs can be created')
def step_impl(context):
    context.cubes.output_all()

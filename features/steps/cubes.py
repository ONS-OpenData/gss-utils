import json

from behave import *
from nose.tools import *
from gssutils import *
from io import BytesIO, SEEK_END, StringIO, TextIOBase


from csvw import run_csv2rdf


def get_fixture(file_name):
    """Helper to get specific files out of the fixtures dir"""
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    fixture_file_path = Path(feature_path, "fixtures", file_name)
    return fixture_file_path


@given('I want to create datacubes from the seed "{seed_name}"')
def step_impl(context, seed_name):
    if hasattr(context, 'codelists'):
        context.cubes = Cubes(get_fixture(seed_name), codelists_path="../" + context.codelists)
    else:
        context.cubes = Cubes(get_fixture(seed_name))


@step('I specify a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}"')
def step_impl(context, cube_name, csv_data, seed_name):
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.read_csv(get_fixture(csv_data))
    suppress_catalog_dsd_output = context.suppress_catalog_dsd_output if "suppress_catalog_dsd_output" in context else False
    context.cubes.add_cube(scraper, df, cube_name, suppress_catalog_and_dsd_output=suppress_catalog_dsd_output)


@step('I add a cube "{cube_name}" with data "{csv_data}" and a scrape seed "{seed_name}" with override containing graph "{override_containing_graph}"')
def step_impl(context, cube_name, csv_data, seed_name, override_containing_graph):
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.read_csv(get_fixture(csv_data))
    suppress_catalog_dsd_output = context.suppress_catalog_dsd_output if "suppress_catalog_dsd_output" in context else False
    context.cubes.add_cube(scraper, df, cube_name, override_containing_graph=override_containing_graph,
                           suppress_catalog_and_dsd_output=suppress_catalog_dsd_output)


@step('the datacube outputs can be created')
def step_impl(context):
    context.cubes.output_all()


@step('generate RDF from the n={n} cube\'s CSV-W output')
def step_impl(context, n):
    n = int(n)
    cube = context.cubes.cubes[n]

    csv_file_path = Path("out") / f'{pathify(cube.title)}.csv'
    metadata_file_path = Path("out") / f'{pathify(cube.title)}.csv-metadata.json'

    csv_io = open(csv_file_path, 'r', encoding='utf-8')
    metadata_io = open(metadata_file_path, 'r', encoding='utf-8')
    context.turtle = run_csv2rdf(str(csv_file_path),
                                 str(metadata_file_path),
                                 csv_io,
                                 metadata_io,
                                 getattr(context, 'codelists', None))

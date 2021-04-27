
from behave import *
from nose.tools import *
from gssutils import *
from io import BytesIO, SEEK_END, StringIO, TextIOBase

from csvw import run_csv2rdf
from gssutils.transform.writers import PMD4Writer, CMDWriter

def get_fixture(file_name):
    """Helper to get specific files out of the fixtures dir"""
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    fixture_file_path = Path(feature_path, "fixtures", file_name)
    return fixture_file_path


def get_write_driver(writer):
    """
    Given a string name fo a driver, returns the class(es) in use
    """
    writer_drivers = {
        "PMD4": PMD4Writer,
        "CMD": CMDWriter,
        "PMD4 and CMD": [PMD4Writer, CMDWriter]
    }
    assert writer in writer_drivers, f'No writer named "{writer}" exists.'
    return writer_drivers[writer]


@given('I want to create "{writer}" datacubes from the seed "{seed_name}"')
def step_impl(context, writer, seed_name):
    context.cubes = Cubes(get_fixture(seed_name), writers=get_write_driver(writer))


@step('I specify a datacube named "{cube_name}" with data "{csv_data}" and a scrape using the seed "{seed_name}"')
def step_impl(context, cube_name, csv_data, seed_name):
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.read_csv(get_fixture(csv_data))
    context.cubes.add_cube(scraper, df, cube_name)


@step('I add a cube "{cube_name}" with data "{csv_data}" and a scrape seed "{seed_name}" with override containing graph "{override_containing_graph}"')
def step_impl(context, cube_name, csv_data, seed_name, override_containing_graph):
    scraper = Scraper(seed=get_fixture(seed_name))
    df = pd.read_csv(get_fixture(csv_data))
    context.cubes.add_cube(scraper, df, cube_name, override_containing_graph=override_containing_graph)


@step('the datacube outputs can be created')
def step_impl(context):
    context.cubes.output_all(raise_writer_exceptions=True)


@step('generate RDF from the n={n} cube\'s CSV-W output')
def step_impl(context, n):
    n = int(n)
    cube = context.cubes.cubes[n]

    csv_file_path = Path("out") / f'{pathify(cube.title)}.csv'
    metadata_file_path = Path("out") / f'{pathify(cube.title)}.csv-metadata.json'

    csv_io = open(csv_file_path, 'r', encoding='utf-8')
    metadata_io = open(metadata_file_path, 'r', encoding='utf-8')
    context.turtle = run_csv2rdf(csv_file_path, metadata_file_path, csv_io, metadata_io)


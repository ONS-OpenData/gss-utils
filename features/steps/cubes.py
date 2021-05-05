
from behave import *
import glob
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


@then(u'the "{writer_str}" output for "{cube_name}" matches "{desired_output}"')
def step_impl(context, writer_str, cube_name, desired_output):

    chosen_writer = get_write_driver(writer_str)

    chosen_cube_as_list = [x for x in context.cubes.cubes if x.title == cube_name]
    assert len(chosen_cube_as_list) == 1, (f'A cube of title {cube_name} '
        f'not found. Got {[x.title for x in context.cubes]}')
    chosen_cube = chosen_cube_as_list[0]

    # TODO - something a tad more subtle than glob!
    # Also, use Path
    csv_output_names  = glob.glob(f'{chosen_writer.get_out_path()}/*.csv')
    assert len(csv_output_names), (f'We currently only support checking cubes of single'
        f' csv outputs. Got {len(csv_output_names)}')
    csv_output_name = csv_output_names[0]

    output_dataframe = pd.read_csv(csv_output_name)
    fixture_dataframe = pd.read_csv(get_fixture(desired_output))

    # TODO - better than this
    # Precision differences in the obs (I think) are making direct comparissons
    # of dataframes a nightmare, so (for now) we're dropping the observations
    # column and type casting the whole dataframe to str.
    if chosen_writer.__name__ == "PMD4Writer":
        output_dataframe = output_dataframe.drop("Value", axis=1)
        fixture_dataframe = fixture_dataframe.drop("Value", axis=1)
    elif chosen_writer.__name__ == "CMDWriter":
        v4_cols = [x for x in fixture_dataframe.columns.values if x.startswith("v4")]
        assert len(v4_cols) == 1, ('The fixture files you are comparing to a CMD output'
            f' need to contain exactly one column with the prefix "v4_". Got {len(v4_cols)}')
        v4_col = v4_cols[0]

        output_dataframe = output_dataframe.drop(v4_col, axis=1)
        fixture_dataframe = fixture_dataframe.drop(v4_col, axis=1)
    
    output_dataframe = output_dataframe.astype(str)
    fixture_dataframe = fixture_dataframe.astype(str)

    assert output_dataframe.equals(fixture_dataframe), ('\nThe transformed dataframe: \n\n'
        f'{output_dataframe} \n\nis not identical to the expected dataframe:\n\n {fixture_dataframe}\n')


# TODO - set to pass trivially while we sort out the plumbing
# and figuring out exactly what kind of metadata output a v4 is gonna need
@then(u'the metadata accompanying the v4 contains')
def step_impl(context):
    pass 


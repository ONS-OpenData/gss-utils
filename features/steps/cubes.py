
import shutil
from behave import *
import logging
import glob
from nose.tools import *
from gssutils import *
from io import BytesIO, SEEK_END, StringIO, TextIOBase

from csvw import run_csv2rdf
from gssutils.transform.writers import PMD4Writer, CMDWriter
from features.fixtures.cubes.formaters import formater_cmd_gdp_example, formater_pmd4_gdp_example

WRITER_DRIVERS = {
        "PMD4": PMD4Writer,
        "CMD": CMDWriter,
        "PMD4 and CMD": [PMD4Writer, CMDWriter]
    }

def get_predefined_formater(formater_name):
    """
    Helper to let us pull cube formatters out of
    fixtures by name
    """
    predefined_formaters = {
        "formater_cmd_gdp_example": formater_cmd_gdp_example,
        "formater_pmd4_gdp_example": formater_pmd4_gdp_example
    }
    return predefined_formaters[formater_name]


def get_fixture(file_name):
    """Helper to get specific files out of the fixtures dir"""
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    fixture_file_path = Path(feature_path, "fixtures", file_name)
    logging.warning(f'Fixture from {fixture_file_path}')
    return fixture_file_path


def select_cube_by_name(context, cube_name):
    """
    Given a name, get the appropriate cube object from the list
    of cubes in context.cubes
    """
    chosen_cube_as_list = [x for x in context.cubes.cubes if x.title == cube_name]
    assert len(chosen_cube_as_list) == 1, (f'A cube of title {cube_name} '
        f'not found. Got {[x.title for x in context.cubes]}')
    return chosen_cube_as_list[0]


def get_write_driver(writer):
    """
    Given a string name fo a driver, returns the class(es) in use
    """
    assert writer in WRITER_DRIVERS, f'No writer named "{writer}" exists.'
    return WRITER_DRIVERS[writer]


@given('I want to create "{writer}" datacubes from the seed "{seed_name}"')
def step_impl(context, writer, seed_name):
    # Note: currently we're using a lot of assumptions around writing outputs
    # then reading them back in for testing.
    # (a) long term - do better (i.e don't do that).
    # (b) short term, clear the Cubes() output directories between writes
    #     to avoid race conditions.
    for writer_driver in [x for x in WRITER_DRIVERS.values() if not isinstance(x, list)]:
        writer_out_path = writer_driver.get_out_path()
        if writer_out_path.exists():
            shutil.rmtree(writer_out_path.absolute())
    context.cubes = Cubes(get_fixture(seed_name), writers=get_write_driver(writer))
    logging.warning(f'Cubes has {context.cubes.formaters}')


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


@given(u'I attach to datacube "{cube_name}" a predefined "{writer_str}" formater named "{formater_name}"')
def step_impl(context, cube_name, writer_str, formater_name):
    chosen_cube = select_cube_by_name(context, cube_name)
    chosen_cube.attached_formaters[writer_str] = get_predefined_formater(formater_name)


@then(u'the "{writer_str}" output for "{cube_name}" matches "{desired_output}"')
def step_impl(context, writer_str, cube_name, desired_output):

    chosen_writer = get_write_driver(writer_str)

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
    # column and type casting the both dataframes to str.
    if chosen_writer.__name__ == "PMD4Writer":
        output_dataframe = output_dataframe.drop("Value", axis=1)
        fixture_dataframe = fixture_dataframe.drop("Value", axis=1)
    elif chosen_writer.__name__ == "CMDWriter":
        v4_cols = [x for x in fixture_dataframe.columns.values if x.lower().startswith("v4")]
        assert len(v4_cols) == 1, ('The fixture files you are comparing to a CMD output'
            f' need to contain exactly one column with the prefix "v4_". Got {len(v4_cols)}')
        v4_col = v4_cols[0]

        assert v4_col in output_dataframe.columns.values, (f'The output does not include the '
            'required V4 prefixed column required. In your fixture this column is specified '
            f'as {v4_col} but output has columns {output_dataframe.columns.values}')

        output_dataframe = output_dataframe.drop(v4_col, axis=1)
        fixture_dataframe = fixture_dataframe.drop(v4_col, axis=1)
    
    output_dataframe = output_dataframe.astype(str)
    fixture_dataframe = fixture_dataframe.astype(str)

    # If this fails they're not equal ..but.. dumping two dataframes to screen won't be much use.
    # Dev note: yes iteration is slow, but this only tiggers if there's a problem, at the point
    # it's worth the wait to see what that problem is
    assert output_dataframe.equals(fixture_dataframe), (f'''
        -- Dataframes do not match --
        Created dataframe:
        {output_dataframe}

        Fixture Dataframe
        {fixture_dataframe}
    ''')

# TODO - set to pass trivially while we sort out the plumbing
# and figuring out exactly what kind of metadata output a v4 is gonna need
@then(u'the metadata accompanying the v4 contains')
def step_impl(context):
    pass 


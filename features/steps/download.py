import json
import os

from behave import *
from nose.tools import *
from urllib.parse import urlparse
import pandas as pd

from gssutils import *
from gssutils.metadata.dcat import get_pmd_periods, get_odata_api_periods, get_principle_dataframe


DEFAULT_RECORD_MODE = 'new_episodes'

def cassette(uri: str) -> str:
    host = urlparse(uri).hostname
    if host in ['www.gss-data.org.uk', '']:
        return f'features/fixtures/cassettes/{host}.yml'
    return 'features/fixtures/scrape.yml'

def get_fixture(file_name: str) -> Path:
    """Helper to get specific files out of the fixtures dir"""
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    fixture_file_path = Path(feature_path, "fixtures", file_name)
    return fixture_file_path

@given('I scrape datasets using info.json "{fixture_path}"')
def step_impl(context, fixture_path: Path):
    context.scraper = Scraper(seed=get_fixture(fixture_path))

@given('the dataset already exists on target PMD')
def step_impl(context):
    # TODO - this. for now I'm leaving it to pass trivially
    pass

@given('caching is set to "{caching_heuristic}"')
def step_impl(context, caching_heuristic):
    # TODO - this. for now I'm leaving it to pass trivially
    pass

@given(u'PMD periods of')
def step_impl(context):
    context.pmd_periods = [x.strip() for x in context.text.split(",")]

@given(u'odata API periods of')
def step_impl(context):
    context.odata_periods = [x.strip() for x in context.text.split(",")]

@given(u'specify the required periods as')
def step_impl(context):
    context.required_periods = [x.strip() for x in context.text.split(",")]

@given('fetch the initial data from the API endpoint')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    context.df = get_principle_dataframe(distro, periods_wanted=context.required_periods)

@given('fetch the supplementary data from the API endpoint')
def step_impl(context):
    # TODO - this
    pass

@then('the data is equal to "{name_of_fixture}"')
def step_impl(context, name_of_fixture):
    df = pd.read_csv(get_fixture(name_of_fixture))
    assert df.equals(context.df), \
        f"Data retrieved does not match data expected. Expected:\n {context.df}\v\nGot:\n{df}"

@then('I identify the periods for that dataset on the API as')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    api_periods = list(set(get_odata_api_periods(distro)))
    expected_periods = [x.strip() for x in context.text.split(",")]
    assert set(pmd_periods) == set(api_periods), \
        f'Expecting "{expected_periods}". \nGot "{api_periods}".'

@then('I identify the periods for that dataset on PMD as')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    pmd_periods = list(set(get_pmd_periods(distro)))
    expected_periods = [x.strip() for x in context.text.split(",")]
    assert set(pmd_periods) == set(expected_periods), \
        f'Expecting "{expected_periods}". \nGot "{pmd_periods}".'

@then(u'the next period to download is "{period_expected}"')
def step_impl(context, period_expected):
    raise NotImplementedError(f'STEP: Then the next period to download is "{period_expected}"')

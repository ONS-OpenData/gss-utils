import json
import os

from behave import *
from nose.tools import *
from urllib.parse import urlparse

from gssutils import *
from gssutils.metadata.dcat import get_pmd_periods, get_odata_api_periods


DEFAULT_RECORD_MODE = 'new_episodes'

# TODO - surely this a pythonic way of doing this?
def compare_unordered_lists(list1: list, list2: list) -> bool:
    """
    Compare two unordered lists, needs to return False where
    a list is None.
    """
    if list1 is None or list2 is None:
        return False
    if len(list1) != len(list2):
        return False
    for item in list1:
        if item not in list2:
            return False
    return True

def cassette(uri: str) -> str:
    host = urlparse(uri).hostname
    if host == 'www.gov.uk':
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

@given('And the dataset already exists on target PMD')
def step_impl(context):
    # TODO - this. for now I'm leaving it to pass trivially
    pass

@then('I identify the periods for that dataset on the API as')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    api_periods = list(set(get_odata_api_periods(distro)))
    expected_periods = [x.strip() for x in context.text.split(",")]
    assert compare_unordered_lists(api_periods, expected_periods), \
        f'Expecting "{expected_periods}". \nGot "{api_periods}".'

@then('I identify the periods for that dataset on PMD as')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    pmd_periods = list(set(get_pmd_periods(distro).sort()))
    expected_periods = [x.strip() for x in context.text.split(",")]
    assert compare_unordered_lists(pmd_periods, expected_periods), \
        f'Expecting "{expected_periods}". \nGot "{pmd_periods}".'


    

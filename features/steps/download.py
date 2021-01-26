import json
import os

import requests
import vcr
from behave import *
from nose.tools import *
from urllib.parse import urlparse
import pandas as pd

from gssutils import *
from gssutils.transform.download import get_pmd_periods, get_odata_api_periods, get_principle_dataframe, \
                    get_supplementary_dataframes, merge_principle_supplementary_dataframes


DEFAULT_RECORD_MODE = 'new_episodes'

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
    with vcr.use_cassette("features/fixtures/cassettes/odata_api.yml",
                record_mode=context.config.userdata.get('record_mode','DEFAULT_RECORD_MODE')):
        context.df = get_principle_dataframe(distro, periods_wanted=context.required_periods)

@given('fetch the supplementary data from the API endpoint')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    with vcr.use_cassette("features/fixtures/cassettes/odata_api.yml",
                record_mode=context.config.userdata.get('record_mode','DEFAULT_RECORD_MODE')):
        context.supplementary_datasets = get_supplementary_dataframes(distro)

@then('the data is equal to "{name_of_fixture}"')
def step_impl(context, name_of_fixture):
    df = pd.read_csv(get_fixture(name_of_fixture))
    assert df.equals(context.df), \
        f"Data retrieved does not match data expected. Expected:\n {context.df}\v\nGot:\n{df}"

@then('I identify the periods for that dataset on the API as')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    with vcr.use_cassette("features/fixtures/cassettes/odata_api.yml",
                    record_mode=context.config.userdata.get('record_mode','DEFAULT_RECORD_MODE')):
        api_periods = list(set(get_odata_api_periods(distro)))
        expected_periods = [x.strip() for x in context.text.split(",")]
        assert set(api_periods) == set(api_periods), \
            f'Expecting "{expected_periods}". \nGot "{api_periods}".'

@then('I identify the periods for that dataset on PMD as')
def step_impl(context):
    distro = context.scraper.distribution(latest=True)
    with vcr.use_cassette("features/fixtures/cassettes/pmd4.yml",
                    record_mode=context.config.userdata.get('record_mode','DEFAULT_RECORD_MODE')):
        pmd_periods = list(set(get_pmd_periods(distro)))
        expected_periods = [x.strip() for x in context.text.split(",")]
        assert set(pmd_periods) == set(expected_periods), \
            f'Expecting "{expected_periods}". \nGot "{pmd_periods}".'

@then('the names and dataframes returned equate to')
def step_impl(context):
    for row in context.table:
        key = row[0]
        fixture_name = row[1]

        df_got = context.supplementary_datasets[key]
        df_expected = pd.read_csv(get_fixture(fixture_name))
        
        assert df_expected == context.supplementary_datasets[key], \
            f'Data for "{key}" does not match expected. Got \n"{df_got}"\n, but expected \n"{df_expected}"\n.'
    
@then(u'I merge the dataframes based on primary keys')
def step_impl(context):
    context.df_merged = merge_principle_supplementary_dataframes(context.df, context.supplementary_datasets)
import os
from urllib.parse import urlparse

import requests
import vcr
from behave import *
from nose.tools import *

from gssutils import Scraper
from gssutils.metadata import DCTERMS, DCAT, RDFS, namespaces
from gssutils.metadata.mimetype import Excel

DEFAULT_RECORD_MODE = 'new_episodes'


def cassette(uri):
    host = urlparse(uri).hostname
    if host == 'www.gov.uk':
        return f'features/fixtures/cassettes/{host}.yml'
    return 'features/fixtures/scrape.yml'


@given('I scrape the page "{uri}"')
def step_impl(context, uri):
    with vcr.use_cassette(cassette(uri),
                          record_mode=context.config.userdata.get('record_mode',
                                                                  DEFAULT_RECORD_MODE)):
        context.scraper = Scraper(uri, requests.Session())


@given('I use the testing seed "{file_name}"')
def step_impl(context, file_name):
    feature_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    seed_path = os.path.join(feature_path, "fixtures", file_name)
    context.scraper = Scraper(seed=seed_path)


@given('I fetch the seed path "{file_name}"')
def step_impl(context, file_name):
    feature_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    seed_path = os.path.join(feature_path, "fixtures", file_name)
    context.seed_path = seed_path


@then('building scrapper should fail with "{error_message}"')
def step_impl(context, error_message):
    captured_error_message = ""
    try:
        context.scrapper = Scraper(seed=context.seed_path)
    except ValueError as err:
        captured_error_message = str(err)
    assert_equal(error_message, captured_error_message)


@then('the data can be downloaded from "{uri}"')
def step_impl(context, uri):
    if not hasattr(context, 'distribution'):
        context.distribution = context.scraper.distribution(latest=True)
    assert_equal(context.distribution.downloadURL, uri)


@then('the data download URL should match "{uri}"')
def step_impl(context, uri):
    if not hasattr(context, 'distribution'):
        context.distribution = context.scraper.distribution(latest=True)
    assert_regexp_matches(context.distribution.downloadURL, uri)


@step('the title should be "{title}"')
def step_impl(context, title):
    assert_equal(context.scraper.title, title)


@step('the title should match "{title}"')
def step_impl(context, title):
    assert_regexp_matches(context.scraper.title, title)


@step('the publication date should match "{date}"')
def step_impl(context, date):
    assert_regexp_matches(context.scraper.publication_date, date)


@step('the next release date should match "{date}"')
def step_impl(context, date):
    assert_regexp_matches(context.scraper.next_release, date)


@step('the description should start "{description}"')
def step_impl(context, description):
    ok_(context.scraper.description.startswith(description))


@step('the contact email address should be "{email}"')
def step_impl(context, email):
    assert_equal(context.scraper.contact, email)


@then("{prefix}:{property} should be `{object}`")
def step_impl(context, prefix, property, object):
    ns = {'dct': DCTERMS, 'dcat': DCAT, 'rdfs': RDFS}.get(prefix)
    assert_equal(context.scraper.dataset.get_property(ns[property]).n3(namespaces), object)


@then("{prefix}:{property} should match `{object}`")
def step_impl(context, prefix, property, object):
    ns = {'dct': DCTERMS, 'dcat': DCAT, 'rdfs': RDFS}.get(prefix)
    assert_regexp_matches(context.scraper.dataset.get_property(ns[property]).n3(namespaces), object)


@step("fetch the distribution as a databaker object")
def step_impl(context):
    with vcr.use_cassette(cassette(context.scraper.uri),
                          record_mode=context.config.userdata.get('record_mode',
                                                                  DEFAULT_RECORD_MODE)):
        if not hasattr(context, 'distribution'):
            context.distribution = context.scraper.distribution(latest=True)
        context.databaker = context.distribution.as_databaker(latest=True)


@then("the sheet names contain [{namelist}]")
def step_impl(context, namelist):
    names = [name.strip() for name in namelist.split(',')]
    tabnames = [tab.name for tab in context.databaker]
    ok_(set(names).issubset(set(tabnames)))


@step("I can access excel_ref '{ref}' in the '{name}' tab")
def step_impl(context, ref, name):
    sheet = [tab for tab in context.databaker if tab.name == name][0]
    assert_true(sheet.excel_ref(ref))


@step("the '{env}' environment variable is '{value}'")
def step_impl(context, env, value):
    os.environ[env] = value


@step("select the distribution given by")
def step_impl(context):
    args = {"latest":True}
    for row in context.table:
        args[row[0]] = row[1]
    context.distribution = context.scraper.distribution(**args)


@step("fetch the '{tabname}' tab as a pandas DataFrame")
def step_impl(context, tabname):
    with vcr.use_cassette(cassette(context.scraper.uri),
                          record_mode=context.config.userdata.get('record_mode',
                                                                  DEFAULT_RECORD_MODE)):
        context.pandas = context.distribution.as_pandas(sheet_name=tabname)


@then("the dataframe should have {rows:d} rows")
def step_impl(context, rows):
    dfrows, dfcols = context.pandas.shape
    eq_(rows, dfrows)


@step('select the distribution whose title starts with "{title_start}"')
def step_impl(context, title_start):
    context.distribution = context.scraper.distribution(latest=True, title=lambda x: x.startswith(title_start))
    assert_is_not_none(context.distribution)


@then("fetch the tabs as a dict of pandas DataFrames")
def step_impl(context):
    with vcr.use_cassette(cassette(context.scraper.uri),
                          record_mode=context.config.userdata.get('record_mode',
                                                                  DEFAULT_RECORD_MODE)):
        context.pandas = context.distribution.as_pandas()
        eq_(type(context.pandas), dict)


@step("all mandatory fields are set")
def step_impl(context):
    unset = list(context.scraper.dataset.get_unset())
    ok_(len(unset) == 0, f"Not all mandatory fields are set: {unset}")


@step("the catalog has more than one dataset")
def step_impl(context):
    eq_(type(context.scraper.catalog.dataset), list)
    assert(len(context.scraper.catalog.dataset) > 1)


@step('I select the dataset "{title}"')
def step_impl(context, title):
    context.scraper.select_dataset(title=title)


@when('I select the dataset whose title starts with "{title}"')
def step_impl(context, title):
    context.scraper.select_dataset(title=lambda x: x.startswith(title))


@when('I select the latest dataset whose title starts with "{title}"')
def step_impl(context, title):
    context.scraper.select_dataset(title=lambda x: x.startswith(title), latest=True)


@step("fetch the distribution as a pandas dataframe")
def step_impl(context):
    with vcr.use_cassette(cassette(context.scraper.uri),
                          record_mode=context.config.userdata.get('record_mode',
                                                                  DEFAULT_RECORD_MODE)):
        context.pandas = context.pandas = context.distribution.as_pandas()


@step('fetch the distribution as a pandas dataframe with encoding "{encoding}"')
def step_impl(context, encoding):
    with vcr.use_cassette(cassette(context.scraper.uri),
                          record_mode=context.config.userdata.get('record_mode',
                                                                  DEFAULT_RECORD_MODE)):
        context.pandas = context.pandas = context.distribution.as_pandas(encoding=encoding)


@then('the dataset landing page should be "{url}"')
def step_impl(context, url):
    eq_(context.scraper.dataset.landingPage, url)

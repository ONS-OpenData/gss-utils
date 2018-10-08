from behave import *
from gssutils import Scraper
from nose.tools import *
import vcr
import requests
from gssutils.metadata import DCTERMS, DCAT, namespaces
import os


@given('I scrape the page "{uri}"')
def step_impl(context, uri):
    with vcr.use_cassette('features/fixtures/scrape.yml', record_mode='new_episodes'):
        context.scraper = Scraper(uri, requests.Session())


@then('the data can be downloaded from "{uri}"')
def step_impl(context, uri):
    if not hasattr(context, 'distribution'):
        context.distribution = context.scraper.distribution()
    assert_equal(context.distribution.downloadURL, uri)


@step('the title should be "{title}"')
def step_impl(context, title):
    assert_equal(context.scraper.title, title)


@step('the publication date should be "{date}"')
def step_impl(context, date):
    assert_equal(context.scraper.publication_date, date)


@step('the next release date should be "{date}"')
def step_impl(context, date):
    assert_equal(context.scraper.next_release, date)


@step('the description should start "{description}"')
def step_impl(context, description):
    ok_(context.scraper.description.startswith(description))


@step('the contact email address should be "{email}"')
def step_impl(context, email):
    assert_equal(context.scraper.contact, email)


@then("{prefix}:{property} should be `{object}`")
def step_impl(context, prefix, property, object):
    ns = {'dct': DCTERMS, 'dcat': DCAT}.get(prefix)
    assert_equal(context.scraper.dataset.get_property(ns[property]).n3(namespaces), object)


@step("fetch the distribution as a databaker object")
def step_impl(context):
    with vcr.use_cassette('features/fixtures/scrape.yml', record_mode='new_episodes'):
        if not hasattr(context, 'distribution'):
            context.distribution = context.scraper.distribution()
        context.databaker = context.distribution.as_databaker()


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
    args = {}
    for row in context.table:
        args[row[0]] = row[1]
    context.distribution = context.scraper.distribution(**args)


@step("fetch the '{tabname}' tab as a pandas DataFrame")
def step_impl(context, tabname):
    with vcr.use_cassette('features/fixtures/scrape.yml', record_mode='new_episodes'):
        context.pandas = context.distribution.as_pandas(sheet_name=tabname)


@then("the dataframe should have {rows:d} rows")
def step_impl(context, rows):
    dfrows, dfcols = context.pandas.shape
    eq_(rows, dfrows)
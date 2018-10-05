from behave import *
from gssutils import Scraper
from nose.tools import *
import vcr
import requests
from gssutils.metadata import DCTERMS, DCAT, namespaces
import os


@given('a dataset page "{uri}"')
def step_impl(context, uri):
    context.scraper = Scraper(uri, requests.Session())


@when("I scrape this page")
def step_impl(context):
    with vcr.use_cassette('features/fixtures/scrape.yml', record_mode='new_episodes'):
        context.scraper.run()


@then('the data can be downloaded from "{uri}"')
def step_impl(context, uri):
    assert_equal(context.scraper.data_uri, uri)


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


@step('select "{extension}" files')
def step_impl(context, extension):
    mediaType = {
        "ODS": "application/vnd.oasis.opendocument.spreadsheet",
        "XLS": "application/vnd.ms-excel",
        "XLSX": "application/vnd.ms-excel"
    }.get(extension)
    context.scraper.dist_filter(mediaType=mediaType)


@step('select files with title "{title}"')
def step_impl(context, title):
    context.scraper.dist_filter(title=title)


@then("{prefix}:{property} should be `{object}`")
def step_impl(context, prefix, property, object):
    ns = {'dct': DCTERMS, 'dcat': DCAT}.get(prefix)
    assert_equal(context.scraper.dataset.get_property(ns[property]).n3(namespaces), object)


@step("fetch the distribution as a databaker object")
def step_impl(context):
    with vcr.use_cassette('features/fixtures/scrape.yml', record_mode='new_episodes'):
        context.databaker = context.scraper.as_databaker


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
    print(context.table)
    d = {}
    for row in context.table:
        d[row[0]] = row[1]
    context.scraper.dist_filter(**d)

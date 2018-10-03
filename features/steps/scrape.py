from behave import *
from gssutils import Scraper
from nose.tools import assert_equal
import vcr
import requests
from gssutils.metadata import DCTERMS, DCAT, namespaces


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


@step('the description should read "{description}"')
def step_impl(context, description):
    assert_equal(context.scraper.description, description)


@step('the contact email address should be "{email}"')
def step_impl(context, email):
    assert_equal(context.scraper.contact, email)


@step('select "{extension}" files')
def step_impl(context, extension):
    mimetype = {
        "ODS": "application/vnd.oasis.opendocument.spreadsheet",
        "XLS": "application/vnd.ms-excel"
    }.get(extension)
    context.scraper.dist_filter(mimeType=mimetype)


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


@then("the sheet names are [{namelist}]")
def step_impl(context, namelist):
    names = [name.strip() for name in namelist.split(',')]
    tabnames = [tab.name for tab in context.databaker]
    assert_equal(names, tabnames)
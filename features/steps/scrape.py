from behave import *
from gssutils import Scraper
from nose.tools import assert_equal

@given(
    'a dataset page "{uri}"')
def step_impl(context, uri):
    context.scraper = Scraper(uri)

@when("I scrape this page")
def step_impl(context):
    context.scraper.run()

@then('the data can be downloaded from "{uri}"')
def step_impl(context, uri):
    assert_equal(context.scraper.dataURI, uri)

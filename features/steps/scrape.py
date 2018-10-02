from behave import *
from gssutils import Scraper
from nose.tools import assert_equal
import vcr
import requests


@given('a dataset page "{uri}"')
def step_impl(context, uri):
    context.scraper = Scraper(uri, requests.Session())


@vcr.use_cassette('features/fixtures/scrape.yml')
@when("I scrape this page")
def step_impl(context):
    with vcr.use_cassette('features/fixtures/scrape.yml'):
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
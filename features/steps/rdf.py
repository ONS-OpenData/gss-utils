from behave import *
from nose.tools import *
from rdflib.compare import to_isomorphic, graph_diff
from rdflib import Graph
from dateutil.parser import parse
from datetime import datetime
from gssutils.metadata import THEME

@step("set the base URI to <{uri}>")
def step_impl(context, uri):
    context.scraper.set_base_uri(uri)


@step("set the dataset ID to <{dataset_id}>")
def step_impl(context, dataset_id):
    context.scraper.set_dataset_id(dataset_id)


@step("set the description to '{description}'")
def step_impl(context, description):
    context.scraper.set_description(description)


@step("generate TriG")
def step_impl(context):
    context.trig = context.scraper.generate_trig()


@then("the TriG should contain")
def step_impl(context):
    g1 = to_isomorphic(Graph().parse(format='trig', data=context.trig))
    g2 = to_isomorphic(Graph().parse(format='trig', data=context.text))
    in_both, only_in_first, only_in_second = graph_diff(g1, g2)
    ok_(len(only_in_second) == 0, f"""
<<<
{only_in_first.serialize(format='n3').decode('utf-8')}
===
{only_in_second.serialize(format='n3').decode('utf-8')}
>>>
""")


@step("the RDF should contain")
def step_impl(context):
    g1 = to_isomorphic(Graph().parse(format='turtle', data=context.turtle))
    g2 = to_isomorphic(Graph().parse(format='turtle', data=context.text))
    in_both, only_in_first, only_in_second = graph_diff(g1, g2)
    ok_(len(only_in_second) == 0, f"""
<<<
{only_in_first.serialize(format='n3').decode('utf-8')}
===
{only_in_second.serialize(format='n3').decode('utf-8')}
>>>
""")


@step("set the family to '{family}'")
def step_impl(context, family):
    context.scraper.set_family(family)


@step("set the theme to <{theme}>")
def step_impl(context, theme):
    context.scraper.set_theme(getattr(THEME, theme))


@step("set the modified time to '{datetime}'")
def step_impl(context, datetime):
    modified = parse(datetime)
    context.scraper.dataset.modified = modified


@step("set the license to '{license}'")
def step_impl(context, license):
    license_url = {
        'OGLv3': 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
    }.get(license)
    context.scraper.dataset.license = license_url


@then("the dataset URI should be <{uri}>")
def step_impl(context, uri):
    eq_(str(context.scraper.dataset.uri), uri)


@step("the metadata graph should be <{uri}>")
def step_impl(context, uri):
    eq_(str(context.scraper.dataset.graph), uri)


@step("the modified date should be quite recent")
def step_impl(context):
    now = datetime.now()
    ok_((abs(now - context.scraper.dataset.modified)).total_seconds() < 60)


@step('the comment should be "{comment}"')
def step_impl(context, comment):
    eq_(context.scraper.dataset.comment, comment)

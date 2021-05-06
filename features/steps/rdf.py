from pathlib import Path

from behave import *
from nose.tools import *
from rdflib.compare import to_isomorphic, graph_diff
from rdflib import Graph
from dateutil.parser import parse
from datetime import datetime, timezone
from gssutils.metadata import THEME
import distutils.util


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


def test_graph_diff(g1, g2):
    in_both, only_in_first, only_in_second = graph_diff(to_isomorphic(g1), to_isomorphic(g2))
    only_in_first.namespace_manager = g1.namespace_manager
    only_in_second.namespace_manager = g2.namespace_manager
    ok_(len(only_in_second) == 0, f"""
<<<
{only_in_first.serialize(format='n3').decode('utf-8')}
===
{only_in_second.serialize(format='n3').decode('utf-8')}
>>>
""")


@then("the TriG should contain")
def step_impl(context):
    test_graph_diff(
        Graph().parse(format='trig', data=context.trig),
        Graph().parse(format='trig', data=context.text)
    )


@then('the TriG at "{trig_file}" should contain')
def step_impl(context, trig_file):
    test_graph_diff(
        Graph().parse(format='trig', source=trig_file),
        Graph().parse(format='trig', data=context.text)
    )


@then('the file at "{file}" should not exist')
def step_impl(context, file):
    assert not Path(file).exists()


@then('the file at "{file}" should exist')
def step_impl(context, file):
    assert Path(file).exists()


@step("the RDF should contain")
def step_impl(context):
    test_graph_diff(
        Graph().parse(format='turtle', data=context.turtle),
        Graph().parse(format='turtle', data=context.text)
    )


@step("the ask query '{query_file}' should return {expected_query_result}")
def step_impl(context, query_file: str, expected_query_result: str):
    query_file = Path('features') / 'fixtures' / query_file
    with open(query_file) as f:
        query = f.read()
    g = Graph().parse(format='turtle', data=context.turtle)
    results = list(g.query(query))
    ask_result = results[0]
    expected_ask_result = bool(distutils.util.strtobool(expected_query_result))
    assert(ask_result == expected_ask_result)


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


@then("the dataset contents URI should be <{uri}>")
def step_impl(context, uri):
    eq_(str(context.scraper.dataset.datasetContents.uri), uri)


@step("the pmdcat:graph should be <{uri}>")
def step_impl(context, uri):
    eq_(str(context.scraper.dataset.pmdcatGraph), uri)


@step("the modified date should be quite recent")
def step_impl(context):
    now = datetime.now(timezone.utc).astimezone()
    ok_((abs(now - context.scraper.dataset.modified)).total_seconds() < 60)


@step('the comment should be "{comment}"')
def step_impl(context, comment):
    eq_(context.scraper.dataset.comment, comment)


@then('the modified date should be around "{date}"')
def step_impl(context, date):
    eq_(context.scraper.dataset.modified.date(), datetime.fromisoformat(date).date())


@then('the TriG should contain triples given by "{turtle_file}"')
def step_impl(context, turtle_file):
    with open(Path('features') / 'fixtures' / turtle_file) as f:
        test_graph_diff(
            Graph().parse(format='trig', data=context.trig),
            Graph().parse(format='turtle', file=f)
        )

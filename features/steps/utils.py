from behave import *
from gssutils import *
from nose.tools import *


@given("a table of labels and corresponding paths")
def step_impl(context):
    context.pathify_tests = context.table


@then("the pathify function should convert labels to paths")
def step_impl(context):
    for row in context.pathify_tests:
        eq_(pathify(row[0]), row[1])

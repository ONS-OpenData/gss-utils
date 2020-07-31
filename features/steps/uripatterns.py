from behave import *
from nose.tools import eq_, assert_in
from uritemplate import URITemplate

from gssutils.csvw.uripattern import URIPattern

use_step_matcher("re")


@given("a URI template (?P<template>.+)")
def step_impl(context, template):
    context.pattern = URIPattern()
    context.pattern.templates.append(URITemplate(template))


@step("a path regular expression (?P<regex>.+)")
def step_impl(context, regex):
    context.pattern.regexes.append(regex)


@then("the (?P<col>.+) column can be validated against (?P<format>.+)")
def step_impl(context, col, format):
    formats = context.pattern.formats()
    assert_in(col, formats, f'Expected a format for {col}')
    eq_(formats[col], format)

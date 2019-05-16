from behave import *
from databaker.jupybakehtml import savepreviewhtml
from nose.tools import *


@then('preview the tab named "{name}"')
def step_impl(context, name):
    tabs = {tab.name: tab for tab in context.databaker}
    savepreviewhtml(tabs[name])
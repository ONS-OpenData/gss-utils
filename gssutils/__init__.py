import functools

from messytables import excel
from messytables.excel import XLSProperties

from gssutils.scrape import Scraper
from gssutils.utils import pathify, is_interactive
from gssutils.schema import CSVWSchema
from databaker.framework import *
import pandas as pd
from gssutils.metadata import Excel, ODS, THEME
from pathlib import Path


# Monkey patch an issue in Messytables that stops us from using savepreviewhtml from Databaker:


def bold_wrapper(old_get_bold):
    @functools.wraps(old_get_bold)
    def new_get_bold(self):
        try:
            return old_get_bold(self)
        except:
            return False

    return new_get_bold


XLSProperties.get_bold = bold_wrapper(XLSProperties.get_bold)

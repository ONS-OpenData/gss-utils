import logging
import mimetypes
import re
from functools import lru_cache
from urllib.parse import urldefrag, urljoin, urlparse

from dateutil.parser import parse
from lxml import html

from gssutils.metadata import Distribution, ODS, Excel, Dataset, PMDDataset, GOV
from gssutils.utils import pathify


def scrape(scraper, tree):

    scraper.dataset.publisher = GOV['department-for-communities-northern-ireland']
    scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-" \
        "government-licence/version/3/'

    # Get the dataset title as the original uri params we used
    scraper.dataset.title = scraper.uri.split("search=%22")[1].split("%22")[0] \
        .replace("+", " ")

    # We're taking each search result as a distribution
    distributions_urls = []
    for linkObj in tree.xpath("//h3/a"):

        # linkObj.items() is eg ("href", "www.foo.com") where we want a url
        href = [x[1] for x in linkObj.items() if x[0] == "href"][0]

        # Add to distributions url list, get the root from the original url
        distributions_urls.append(scraper.uri.split("/publications/topic")[0] + href)

    # Create the individual distributions from the distributions urls
    for url in distributions_urls:

        # Get the distribution page
        page = scraper.session.get(url)
        distro_tree = html.fromstring(page.text)

        # Create our new distribution object
        this_distribution = Distribution(scraper)

        this_distribution.title = distro_tree.xpath("//title/text()")[0]

        # Get the ODS link (and confirm there's just one)
        spreadsheet_files = [x for x in distro_tree.xpath('//a/@href') if x.lower().endswith(".ods") or x.lower().endswith(".xlsx")]

        # There should be exactly one spreadsheet file (the download for this distribution)
        if len(spreadsheet_files) == 0:
            # There's no .ods, .xlsx or .xls files - it's not a dataset
            break
        elif len(spreadsheet_files) > 1:
            # We should only ever have 1 ods or xls file. Abort if that pattern is broken.
            raise Exception("Webpage '{}' has an unexpected number of spreadsheets. Aborting scrape.".format(url))
        this_distribution.downloadURL = spreadsheet_files[0]

        if this_distribution.downloadURL.lower().endswith(".xlsx"):
            media_type = Excel
        elif this_distribution.downloadURL.lower().endswith(".ods"):
            media_type = ODS
        else:
            raise Exception("Aborting. Unexpected media type for url: '{}'"
                            .format(this_distribution.downloadURL))
        this_distribution.mediaType = media_type

        # Published and modifed time
        this_distribution.issued = distro_tree.xpath("//*[@property='article:published_time']/@content")[0]
        this_distribution.modified = distro_tree.xpath("//*[@property='article:modified_time']/@content")[0]
        this_distribution.description = distro_tree.xpath("//*[@class='field-summary']/p/text()")[0]

        scraper.distributions.append(this_distribution)

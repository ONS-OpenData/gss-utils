import mimetypes
import re
from datetime import datetime
from functools import lru_cache

from dateutil.parser import parse, isoparse
from lxml import html

from gssutils.metadata.mimetype import ODS
from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution
import gssutils.scrapers

FILE_TYPE_AND_SIZE_RE = re.compile(r'.*file type:\s+([^\s]+),\s+file size:\s+([0-9]+)\s+(\w+)', re.DOTALL)


def scrape(scraper, tree):
    # It's not clear whether the pages are collections of datasets or datasets with distributions.
    # Assume the latter for simplicity for now.
    scraper.dataset.publisher = GOV['welsh-government']
    # OGLv3 license is quoted for the whole site on https://gov.wales/copyright-statement
    scraper.dataset.rights = "https://gov.wales/copyright-statement"
    scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
    scraper.dataset.title = tree.xpath('//h1//text()')[0].strip()
    scraper.dataset.description = tree.xpath(
        "//div[contains(concat(' ', @class, ' '), ' hero-block__summary ')]/div/p/text()")[0].strip()
    meta = tree.xpath("//div[@class='header-meta']")[0]
    published = meta.xpath(
        "div[contains(concat(' ', @class, ' '), ' first-published ')]/" + \
        "div[contains(concat(' ', @class, ' '), ' item ')]/text()")[0].strip()
    scraper.dataset.issued = parse(published, parserinfo=gssutils.scrapers.UK_DATES)
    updated = meta.xpath(
        "div[contains(concat(' ', @class, ' '), ' last-updated ')]/" + \
        "div[contains(concat(' ', @class, ' '), ' item ')]//time/@datetime")[0].strip()
    scraper.dataset.modified = isoparse(updated)

    @lru_cache()
    def fetch_page(url):
        page = scraper.session.get(url)
        return html.fromstring(page.text)

    for article in tree.xpath("//div[@role='article']"):
        title_div = article.xpath("div[@class = 'index-list__title']")[0]
        meta_div = article.xpath("div[@class = 'index-list__meta']")[0]
        release_page = fetch_page(title_div.xpath('a/@href')[0])
        for details in release_page.xpath(
                "//div[@id = 'release--data']//div[@class = 'document__details']"):
            distribution = Distribution(scraper)
            distribution.downloadURL = details.xpath("h3/a/@href")[0]
            distribution.title = details.xpath("h3/a/div/text()")[0].strip()
            distribution.issued = isoparse(details.xpath(
                "//div[contains(concat(' ', @class, ' '), ' meta__released ')]//time/@datetime")[0])
            distribution.modified = isoparse(details.xpath(
                "//div[contains(concat(' ', @class, ' '), ' meta__update_history ')]//time/@datetime")[0])
            dist_meta = details.xpath("h3/a/span/text()")[0].strip()
            meta_match = FILE_TYPE_AND_SIZE_RE.match(dist_meta)
            if meta_match:
                distribution.mediaType = {'ODS': ODS}.get(meta_match.group(1))
                size_qualifier = meta_match.group(3)
                size = float(meta_match.group(2))
                if size_qualifier == "KB":
                    distribution.byteSize = int(size * 1024)
                elif size_qualifier == "kB":
                    distribution.byteSize = int(size * 1000)
            else:
                distribution.mediaType, _ = mimetypes.guess_type(distribution.downloadURL)
            scraper.distributions.append(distribution)

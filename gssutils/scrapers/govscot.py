import mimetypes
import re
from urllib.parse import urljoin

from dateutil.parser import parse

from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution
import gssutils.scrapers


def scrape(scraper, tree):
    scraper.dataset.publisher = GOV['the-scottish-government']
    scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
    scraper.dataset.title = tree.xpath(
        "//div[@id='body2']//h2/text()")[0].strip()
    scraper.dataset.description = scraper.to_markdown(tree.xpath(
        "//div[@id='body2']//h2/following-sibling::div/child::div"))
    doctable = tree.xpath(
        "//table[contains(concat(' ', @class, ' '), ' dg file ')]")[0]
    for row in doctable.xpath('tr'):
        try:
            if row.xpath('th/text()')[0].strip() == 'File:':
                cell = row.xpath('td')[0]
                dist = Distribution(scraper)
                title_size_date = re.compile(r'(.*)\[([^,]+),\s+([0-9.]+)\s+([^:]+):\s([^\]]+)')
                match = title_size_date.match(cell.text_content())
                if match:
                    dist.title = match.group(1)
                    scraper.dataset.issued = parse(match.group(5), parserinfo=gssutils.scrapers.UK_DATES).date()
                dist.downloadURL = urljoin(scraper.uri, cell.xpath('a/@href')[0])
                dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
                scraper.distributions.append(dist)
        except:
            break

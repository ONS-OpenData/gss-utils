import logging
import mimetypes
import re
from functools import lru_cache
from urllib.parse import urldefrag, urljoin, urlparse

from dateutil.parser import parse
from lxml import html

from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import Excel
from gssutils.metadata.pmdcat import Dataset


def scrape(scraper, tree):
    size_re = re.compile(r'\[([0-9]+)(kb|Mb)\]')
    scraper.catalog.title = tree.xpath('//h2/text()')[0].strip()
    scraper.catalog.uri = scraper.uri + "#catalog"
    scraper.catalog.rights = 'http://www.isdscotland.org/Copyright.asp'
    scraper.catalog.publisher = GOV['information-services-division-scotland']
    title2dataset = {}

    @lru_cache()
    def fetch_page(url):
        page = scraper.session.get(url)
        return html.fromstring(page.text)

    for record in tree.xpath("//div[contains(concat(' ', @class, ' '), ' pubtitlel ')]"):
        dataset_title = record.text.strip()
        if dataset_title not in title2dataset:
            dataset = Dataset(scraper.uri)
            dataset.title = dataset_title
            dataset.publisher = scraper.catalog.publisher
            dataset.rights = scraper.catalog.rights
            dataset.distribution = []
            title2dataset[dataset_title] = dataset
        else:
            dataset = title2dataset[dataset_title]

        datatables_urls = record.xpath("following-sibling::table/descendant::tr[td["
                                       "contains(text(), 'Data Tables')]]/td["
                                       "contains(concat(' ', @class, ' '), 'pubcontentr')]/a/@href")
        if len(datatables_urls) == 0:
            continue
        doc_url, frag = urldefrag(urljoin(scraper.uri, datatables_urls[0]))
        # pages appear to have redundant query parameter the same as the fragment id
        doc_url_bits = urlparse(doc_url)
        if doc_url_bits.query is not None and doc_url_bits.query == f'id={frag}':
            doc_url = doc_url_bits._replace(query=None).geturl()
        doc_tree = fetch_page(doc_url)
        anchors = doc_tree.xpath(f"//a[@id='{frag}' or @name='{frag}']")
        if len(anchors) == 0:
            logging.warning(f"Broken link to dataset {datatables_urls[0]}")
            continue

        # publication date is in paragraph before!
        # this is actually the issued date of the distribution
        published = anchors[0].xpath("../preceding-sibling::p[1]/child::*/text()")
        dist_issued = None
        if len(published) > 0 and published[0].startswith('Published '):
            dist_issued = parse(published[0][len('Published '):], dayfirst=True)
            # we'll use the latest publication date for the dataset
            if not (hasattr(dataset, 'issued') and dist_issued <= dataset.issued):
                dataset.issued = dist_issued
        dist_rows = anchors[0].xpath("../following-sibling::table[1]/descendant::tr")
        for row in dist_rows:
            distribution = Distribution(scraper)
            cells = row.xpath('td')
            if len(cells) == 4:
                title_node, download_node, type_node, size_node = cells
            elif len(cells) == 3:
                title_node, download_node, type_node = cells
                size_node = None
            else:
                break
            distribution.title = title_node.text
            if dist_issued is not None:
                distribution.issued = dist_issued
            distribution.downloadURL = download_node[0].get('href')
            type_image = type_node[0].get('src').lower()
            if 'excel' in type_image:
                distribution.mediaType = Excel
            elif 'swf' in type_image:
                distribution.mediaType = 'application/vnd.adobe.flash.movie'
            else:
                distribution.mediaType, encoding = mimetypes.guess_type(distribution.downloadURL)
            if size_node is not None and size_node.text is not None:
                size_match = size_re.match(size_node.text)
                if size_match:
                    if size_match.group(2) == 'Mb': # should be MB
                        distribution.byteSize = int(size_match.group(1)) * 1000000 # https://en.wikipedia.org/wiki/Megabyte MB = 10^6 bytes
                    elif size_match.group(2) == 'kb': # should be either kB or KB    https://en.wikipedia.org/wiki/Kilobyte kB = 1000 while KB = 1024
                        distribution.byteSize = int(size_match.group(1)) * 1000
            dataset.distribution.append(distribution)

    scraper.catalog.dataset = list(title2dataset.values())

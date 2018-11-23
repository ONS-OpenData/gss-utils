import logging
import re
from functools import lru_cache
from urllib.parse import urldefrag, urljoin, urlparse

from dateutil.parser import parse
from lxml import html

from gssutils.metadata import Distribution, PDF, Excel, Dataset


def scrape(scraper, tree):
    size_re = re.compile(r'\[([0-9]+)(kb|Mb)\]')
    scraper.catalog.title = tree.xpath('//h1/text()')[0]
    scraper.catalog.dataset = []
    scraper.catalog.uri = scraper.uri + "#catalog"

    @lru_cache()
    def fetch_page(url):
        page = scraper.session.get(url)
        return html.fromstring(page.text)

    for record in tree.xpath("//div[contains(concat(' ', @class, ' '), ' pubtitlel ')]"):
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
        dataset = Dataset()
        dataset.uri = urljoin(scraper.uri, doc_url)
        dataset.distribution = []
        # publication date is in paragraph before!
        published = anchors[0].xpath("../preceding-sibling::p[1]/child::*/text()")
        if len(published) > 0 and published[0].startswith('Published '):
            dataset.issued = parse(published[0][len('Published '):])
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
            distribution.downloadURL = download_node[0].get('href')
            type_image = type_node[0].get('src').lower()
            if 'excel' in type_image:
                distribution.mediaType = Excel
            elif 'swf' in type_image:
                distribution.mediaType = 'application/vnd.adobe.flash.movie'
            if size_node is not None and size_node.text is not None:
                size_match = size_re.match(size_node.text)
                if size_match:
                    if size_match.group(2) == 'Mb': # should be MB
                        distribution.byteSize = int(size_match.group(1)) * 1000000 # https://en.wikipedia.org/wiki/Megabyte MB = 10^6 bytes
                    elif size_match.group(2) == 'kb': # should be either kB or KB    https://en.wikipedia.org/wiki/Kilobyte kB = 1000 while KB = 1024
                        distribution.byteSize = int(size_match.group(1)) * 1000
            dataset.distribution.append(distribution)
        scraper.catalog.dataset.append(dataset)

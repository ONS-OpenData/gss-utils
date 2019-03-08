import mimetypes
from urllib.parse import urljoin
from dateutil.parser import parse
from gssutils.metadata import Distribution, Excel, ODS, GOV
import re


def scrape(scraper, tree):
    scraper.dataset.title = tree.xpath(
        "//h1/text()")[0].strip()
    scraper.dataset.issued = parse(tree.xpath(
        "//span[text() = 'Date published: ']/following-sibling::span/text()")[0].strip()).date()
    scraper.dataset.keyword = ', '.join(tree.xpath(
        "//div[text()='Statistics: ']/following-sibling::ul/li/a/text()"))
    scraper.dataset.description = scraper.to_markdown(tree.xpath(
        "//div[contains(concat(' ', @class, ' '), ' publicationDetails ')]/div[@class='summary']/div/*"))
    scraper.dataset.publisher = str(GOV["northern-ireland-statistics-and-research-agency"])
    for anchor in tree.xpath(
            "//div[contains(concat(' ', @class, ' '), ' publicationDocs ')]/div[@class='summary']/div//a"):
        dist = Distribution(scraper)
        dist.title = anchor.xpath('text()')[0].strip()
        dist.downloadURL = anchor.get('href')
        type_size_re = re.compile(r'(.*?)\s*\(([^)]+)\)')
        m = type_size_re.match(anchor.xpath('span/text()')[0].strip())
        if m:
            if m.group(1) == 'Excel':
                dist.mediaType = Excel
            else:
                dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
            size = m.group(2)
            if size.strip() != '':
                if size.upper().endswith(' KB'): # https://en.wikipedia.org/wiki/Kilobyte kB = 1000 while KB = 1024
                    dist.byteSize = int(float(size[:-3]) * 1024)
                elif size.upper().endswith(' MB'): # https://en.wikipedia.org/wiki/Megabyte MB = 10^6 bytes
                    dist.byteSize = int(float(size[:-3]) * 1000000)
        scraper.distributions.append(dist)

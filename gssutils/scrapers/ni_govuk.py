from dateutil.parser import parse
from gssutils.metadata import Distribution, PDF, Excel, GOV
import re

type_size_re = re.compile(r"([^\s]*)\s+\(([0-9\.]+)\s+([KMG]B)")


def scrape(scraper, tree):
    scraper.dataset.title = tree.xpath("//h1/text()")[0].strip()
    scraper.dataset.issued = parse(tree.xpath(
        "//p[contains(concat(' ', @class, ' '), ' date-pub ')]/span[@class='date-display-single']/text()")[0]).date()
    scraper.dataset.publisher = GOV['department-of-health-northern-ireland']
    for doc_link in tree.xpath(
            "//div[contains(concat(' ', @class, ' '), ' publicationDocs ')]"
            "//div[contains(concat(' ', @class, ' '), ' nigovfile ')]/a"):
        dist = Distribution(scraper)
        dist.downloadURL = doc_link.get('href')
        dist.title = doc_link.xpath("text()")[0].strip()
        type_size = doc_link.xpath("span[@class='meta']/text()")[0].strip()
        match = type_size_re.match(type_size)
        if match:
            if match.group(1) == 'PDF':
                dist.mediaType = PDF
            elif match.group(1) == 'Excel':
                dist.mediaType = Excel
            size = float(match.group(2))
            if match.group(3) == 'KB':  # https://en.wikipedia.org/wiki/Kilobyte kB = 1000 while KB = 1024
                dist.byteSize = int(size * 1024)
            elif match.group(3) == 'MB':  # https://en.wikipedia.org/wiki/Megabyte MB = 10^6 bytes
                dist.byteSize = int(size * 1000000)
            elif match.group(3) == 'GB':  # https://en.wikipedia.org/wiki/Gigabyte GB = 10^9 bytes
                dist.byteSize = int(size * 1000000000)
        scraper.distributions.append(dist)

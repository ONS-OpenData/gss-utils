import mimetypes
import re
from dateutil.parser import parse

from gssutils.metadata import Distribution, ODS, ZIP, Excel, PDF
from urllib.parse import urljoin


def scrape_common(scraper, tree):
    date_re = re.compile(r'[0-9]{1,2} (January|February|March|April|May|June|' +
                         'July|August|September|October|November|December) [0-9]{4}')
    scraper.dataset.title = tree.xpath("//h1/text()")[0].strip()
    scraper.dataset.comment = tree.xpath("//p[contains(@class, 'lead-paragraph')]/text()")[0].strip()
    dates = tree.xpath("//div[contains(concat(' ', @class, ' '), 'app-c-published-dates')]/text()")
    if len(dates) > 0 and dates[0].strip().startswith('Published '):
        match = date_re.search(dates[0])
        if match:
            scraper.dataset.issued = parse(match.group(0)).date()
    #if len(dates) > 1 and dates[1].strip().startswith('Last updated '):
    #    match = date_re.search(dates[1])
    #    if match:
    #        scraper.dataset.modified = parse(match.group(0)).date()
    from_link = tree.xpath(
        "//span[contains(concat(' ', @class, ' '), 'app-c-publisher-metadata__definition-sentence')]/a/@href")
    if len(from_link) > 0:
        scraper.dataset.publisher = urljoin(scraper.uri, from_link[0])
    licenses = tree.xpath("//a[@rel='license']/@href")
    if len(licenses) > 0:
        scraper.dataset.license = licenses[0]


def scrape_stats(scraper, tree):
    scrape_common(scraper, tree)
    for attachment_section in tree.xpath("//section[contains(concat(' ', @class, ' '), 'attachment')]"):
        distribution = Distribution(scraper)
        distribution.downloadURL = urljoin(scraper.uri, attachment_section.xpath(
            "div/h2[@class='title']/a/@href")[0].strip())
        distribution.title = attachment_section.xpath("div/h2[@class='title']/a/text()")[0].strip()
        fileType = attachment_section.xpath(
            "div/p[@class='metadata']/span[@class='type']/descendant-or-self::*/text()")
        if fileType is not None and len(fileType) > 0:
            if 'Excel' in fileType:
                distribution.mediaType = Excel
            elif 'PDF' in fileType:
                distribution.mediaType = PDF
        if not hasattr(distribution, 'mediaType') or distribution.mediaType is None:
            distribution.mediaType, encoding = mimetypes.guess_type(distribution.downloadURL)
        scraper.distributions.append(distribution)
    next_release_nodes = tree.xpath("//p[starts-with(text(), 'Next release of these statistics:')]/text()")
    if next_release_nodes and (len(next_release_nodes) > 0):
        scraper.dataset.updateDueOn = parse(
            next_release_nodes[0].strip().split(':')[1].split('.')[0].strip()
        ).date()
    scraper.dataset.description = scraper.to_markdown(tree.xpath(
        "//h2[text() = 'Details']/following-sibling::div")[0])


def scrape_sds(scraper, tree):
    scrape_common(scraper, tree)
    for attachment_link in tree.xpath("//span[contains(concat(' ', @class, ' '), ' attachment-inline ')]/a"):
        dist = Distribution(scraper)
        dist.title = attachment_link.text.strip()
        dist.downloadURL = urljoin(scraper.uri, attachment_link.get('href'))
        filetype = attachment_link.getparent().xpath("span[@class='type']//text()")[0].strip()
        if filetype == 'ODS':
            dist.mediaType = ODS
        elif filetype == 'ZIP':
            dist.mediaType = ZIP
        elif filetype == 'MS Excel Spreadsheet':
            dist.mediaType = Excel
        scraper.distributions.append(dist)
    email_link = tree.xpath("//div[contains(concat(' ', @class, ' '), ' contact ')]//a[@class='email']")[0]
    scraper.dataset.contactPoint = email_link.get('href')


def scrape_collection(scraper, tree):
    date_re = re.compile(r'[0-9]{1,2} (January|February|March|April|May|June|' +
                         'July|August|September|October|November|December) [0-9]{4}')
    scraper.catalog.title = tree.xpath("//h1/text()")[0].strip()
    scraper.catalog.comment = tree.xpath('//p[contains(concat(" ", @class, " "), " gem-c-lead-paragraph ")]/text()')[0].strip()
    dates = tree.xpath("//div[contains(concat(' ', @class, ' '), 'app-c-published-dates')]/text()")
    if len(dates) > 0 and dates[0].strip().startswith('Published '):
        match = date_re.search(dates[0])
        if match:
            scraper.dataset.issued = parse(match.group(0)).date()
    doclist = tree.xpath('//ol[@class="gem-c-document-list"]/li/a')
    scraper.catalog.dataset = []
    for doc in doclist:
        if doc.get('href').startswith('/government/statistics'):
            from gssutils import Scraper
            ds_scraper = Scraper(urljoin(scraper.uri, doc.get('href')))
            ds = ds_scraper.dataset
            ds.distribution = ds_scraper.distributions
            scraper.catalog.dataset.append(ds)

import re
from dateutil.parser import parse
from gssutils.metadata import Distribution
from urllib.parse import urljoin


def scrape(scraper, tree):
    date_re = re.compile(r'[0-9]{1,2} (January|February|March|April|May|June|' +
                         'July|August|September|October|November|December) [0-9]{4}')
    scraper.dataset.title = tree.xpath("//h1/text()")[0].strip()
    dates = tree.xpath("//div[contains(concat(' ', @class, ' '), 'app-c-published-dates')]/text()")
    if len(dates) > 0 and dates[0].strip().startswith('Published '):
        match = date_re.search(dates[0])
        if match:
            scraper.dataset.issued = parse(match.group(0)).date()
    if len(dates) > 1 and dates[1].strip().startswith('Last updated '):
        match = date_re.search(dates[1])
        if match:
            scraper.dataset.modified = parse(match.group(0)).date()
    for attachment_section in tree.xpath("//section[contains(concat(' ', @class, ' '), 'attachment')]"):
        distribution = Distribution(scraper)
        distribution.downloadURL = urljoin(scraper.uri, attachment_section.xpath(
            "div/h2[@class='title']/a/@href")[0].strip())
        distribution.title = attachment_section.xpath("div/h2[@class='title']/a/text()")[0].strip()
        fileExtension = attachment_section.xpath(
            "div/p[@class='metadata']/span[@class='type']/descendant-or-self::*/text()")[0].strip()
        distribution.mediaType = {
            'ODS': 'application/vnd.oasis.opendocument.spreadsheet',
            'XLS': 'application/vnd.ms-excel',
            'XLSX': 'application/vnd.ms-excel'
        }.get(fileExtension, fileExtension)
        scraper.distributions.append(distribution)
    next_release_nodes = tree.xpath("//p[starts-with(text(), 'Next release of these statistics:')]/text()")
    if next_release_nodes and (len(next_release_nodes) > 0):
        scraper.dataset.nextUpdateDue = parse(
            next_release_nodes[0].strip().split(':')[1].split('.')[0].strip()
        ).date()
    scraper.dataset.description = scraper.to_markdown(tree.xpath(
        "//h2[text() = 'Details']/following-sibling::div")[0])
    from_link = tree.xpath(
        "//span[contains(concat(' ', @class, ' '), 'app-c-publisher-metadata__definition_sentence')]/a/@href")
    if len(from_link) > 0:
        scraper.dataset.publisher = urljoin(scraper.uri, from_link[0])

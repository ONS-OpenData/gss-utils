from urllib.parse import urljoin
from dateutil.parser import parse
from gssutils.metadata import Distribution


def scrape(scraper, tree):
    scraper.dataset.title = tree.xpath(
        "//h1/text()")[0].strip()
    scraper.dataset.issued = parse(tree.xpath(
        "//span[text() = 'Release date: ']/parent::node()/text()")[1].strip()).date()
    scraper.dataset.nextUpdateDue = parse(tree.xpath(
        "//span[text() = 'Next release: ']/parent::node()/text()")[1].strip()).date()
    scraper.dataset.contactPoint = tree.xpath(
        "//span[text() = 'Contact: ']/following-sibling::a[1]/@href")[0].strip()
    scraper.dataset.comment = tree.xpath(
        "//h2[text() = 'About this dataset']/following-sibling::p/text()")[0].strip()
    distribution = Distribution(scraper)
    distribution.downloadURL = urljoin(scraper.uri, tree.xpath(
        "//a[starts-with(@title, 'Download as xls')]/@href")[0].strip())
    distribution.mediaType = 'application/vnd.ms-excel'
    distribution.title = scraper.dataset.title
    scraper.distributions.append(distribution)
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'

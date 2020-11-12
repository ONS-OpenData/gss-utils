import mimetypes
from urllib.parse import urljoin

from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution
from dateutil.parser import parse
from gssutils.metadata.mimetype import *
import re

from lxml import html

ACCEPTED_MIMETYPES = [ODS, Excel, ExcelOpenXML, ExcelTypes, ZIP, CSV, CSDB]

def statistics_handler(scraper, tree):
    scraper.dataset.publisher = GOV['national-records-of-scotland']
    scraper.dataset.title = tree.xpath('//div[@property = "dc:title"]/h2/text()')[0].strip()
    scraper.dataset.description = tree.xpath('//*[@id="block-system-main"]/div/div/div/div[2]/div/div/p[2]/text()')[0].strip()

    contact = tree.xpath('//*[@id="node-stats-home-page-3022"]/div[2]/div/div/p[10]/a')
    for i in contact:
        scraper.dataset.contactPoint = i.attrib['href']

    if tree.xpath(".//a[text()='Excel']") or tree.xpath(".//a[text()='CSV']"):
        nodes = tree.xpath(".//a[text()='Excel']") + tree.xpath(".//a[text()='CSV']")

        for node in nodes:
            file_type = node.text.lower()
            if file_type in ['excel', 'csv']:
                distribution = Distribution(scraper)
                distribution.title = node.getparent().xpath('.//strong/text()')[0].strip()
                distribution.downloadURL = urljoin(scraper.uri, node.attrib['href'])
                distribution.issued = parse(tree.xpath('//*[@id="block-system-main"]/div/div/div/div[2]/div/div/p[1]/text()')[0].strip()).date()
                if 'Last update' in tree.xpath('//*[@id="block-system-main"]/div/div/div/div[2]/div/div/p[1]/text()'):
                    distribution.issued = parse(
                        tree.xpath('//*[@id="block-system-main"]/div/div/div/div[2]/div/div/p[1]/text()')[0]).date()
                distribution.mediaType = {
                    'csv': 'text/csv',
                    'excel': 'application/vnd.ms-excel'
                }.get(
                    file_type,
                    mimetypes.guess_type(distribution.downloadURL)[0]
                )
                if distribution.mediaType in ACCEPTED_MIMETYPES:
                    scraper.distributions.append(distribution)
                else:
                    pass

    elif tree.findall('.//*[@id="node-stats-home-page-3022"]/div[2]/div/div/p/a'):
        for publication in tree.findall('.//*[@id="node-stats-home-page-3022"]/div[2]/div/div/p/a'):
            if publication.attrib['href'].startswith('/statistics-and-data/statistics/'):
                url = urljoin("https://www.nrscotland.gov.uk/", publication.attrib['href'])
                r = scraper.session.get(url)
                if r.status_code != 200:
                    raise Exception(
                        'Failed to get url {url}, with status code "{status_code}".'.format(url=url,
                                                                                            status_code=r.status_code))
                pubTree = html.fromstring(r.text)

                if pubTree.xpath(".//a[text()='Excel']") or pubTree.xpath(".//a[text()='CSV']"):
                    nodes = pubTree.xpath(".//a[text()='Excel']") + pubTree.xpath(".//a[text()='CSV']")

                    for node in nodes:
                        file_type = node.text.lower()
                        if file_type in ['excel', 'csv']:
                            distribution = Distribution(scraper)
                            distribution.title = scraper.dataset.title + ' ' + publication.text + ' ' + node.text
                            distribution.downloadURL = urljoin(scraper.uri, node.attrib['href'])
                            if 'Last update' in pubTree.xpath(
                                    '//*[@id="block-system-main"]/div/div/div/div[2]/div/div/p/strong/text()')[0]:
                                distribution.issued = parse(pubTree.xpath(
                                    '//*[@id="block-system-main"]/div/div/div/div[2]/div/div/p[1]/text()')[0]).date()
                            else:
                                try:
                                    distribution.issued = parse(re.search('\(([^)]+)', publication.getparent().text_content()).group(1)).date()
                                except:
                                    pass
                            distribution.mediaType = {
                                'csv': 'text/csv',
                                'excel': 'application/vnd.ms-excel'
                            }.get(
                                file_type,
                                mimetypes.guess_type(distribution.downloadURL)[0]
                            )
                            if distribution.mediaType in ACCEPTED_MIMETYPES:
                                scraper.distributions.append(distribution)
                            else:
                                pass
                    else:
                        pass
            else:
                pass
    else:

        for dataset in tree.xpath(".//*[@href[contains(.,'/files/statistics/')]]"):

            distribution = Distribution(scraper)
            distribution.title = dataset.text
            distribution.downloadURL = dataset.attrib['href']
            distribution.mediaType, encoding = mimetypes.guess_type(distribution.downloadURL)
            distribution.issued = scraper.dataset.issued
            if distribution.mediaType in ACCEPTED_MIMETYPES:
                scraper.distributions.append(distribution)
            else:
                pass


def covid_handler(scraper, tree):
    scraper.dataset.publisher = GOV['national-records-of-scotland']
    scraper.dataset.title = tree.xpath('//*[@id="node-stats-home-page-3315"]/div[1]/div/div/h2/text()')[0].strip()
    scraper.dataset.description = tree.xpath('//*[@id="node-stats-home-page-3315"]/div[2]/div/div/p[4]/text()')[0].strip() #TEMP as no description on page is more applicable

    pubDate = tree.xpath('//*[@id="node-stats-home-page-3315"]/div[2]/div/div/p[1]/text()')[0]
    nextDue = tree.xpath('//*[@id="node-stats-home-page-3315"]/div[2]/div/div/p[1]/text()')[2]
    scraper.dataset.issued = parse(pubDate).date()
    scraper.dataset.updateDueOn = parse(nextDue).date()

    contact = tree.xpath('//*[@id="node-stats-home-page-3315"]/div[2]/div/div/p[11]/a')
    for i in contact:
        scraper.dataset.contactPoint = i.attrib['href']

    dataNodes = tree.findall('.//*[@id="node-stats-home-page-3315"]/div[2]/div/div/table/tbody/tr[1]/td[4]/p[2]/a')

    for node in dataNodes:
        file_type = node.text.lower()
        if file_type in ['excel', 'csv']:
            distribution = Distribution(scraper)
            distribution.title = scraper.dataset.title + ' ' + node.text
            distribution.downloadURL = urljoin(scraper.uri, node.attrib['href'])
            distribution.issued = scraper.dataset.issued
            distribution.mediaType = {
                'csv': 'text/csv',
                'excel': 'application/vnd.ms-excel'
            }.get(
                file_type,
                mimetypes.guess_type(distribution.downloadURL)[0]
            )
            scraper.distributions.append(distribution)


def old_statistics_handler(scraper, tree):
    scraper.dataset.publisher = GOV['national-records-of-scotland']
    scraper.dataset.title = tree.xpath('//div[@property = "dc:title"]/h2/text()')[0].strip()
    after_background = tree.xpath(
        '//h3[contains(descendant-or-self::*[text()], "Background")]/following-sibling::*')
    description_nodes = []
    for node in after_background:
        if node.tag != 'h3':
            description_nodes.append(node)
        else:
            break
    scraper.dataset.description = scraper.to_markdown(description_nodes)
    data_nodes = tree.xpath(
        '//h3[contains(descendant-or-self::*[text()], "Data")]/following-sibling::*/child::strong')
    for node in data_nodes:
        for anchor in node.xpath('following-sibling::a'):
            file_type = anchor.text.strip().lower()
            if file_type in ['excel', 'csv']:
                distribution = Distribution(scraper)
                distribution.downloadURL = urljoin(scraper.uri, anchor.get('href'))
                distribution.title = node.text.strip()
                distribution.mediaType = {
                    'csv': 'text/csv',
                    'excel': 'application/vnd.ms-excel'
                }.get(
                    file_type,
                    mimetypes.guess_type(distribution.downloadURL)[0]
                )
                scraper.distributions.append(distribution)

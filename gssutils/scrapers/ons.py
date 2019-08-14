import logging
import mimetypes
import re
from urllib.parse import urljoin

from dateutil.parser import parse

from gssutils.metadata import Distribution, Excel, ODS, CSV, CSDB


def scrape(scraper, tree):
    scraper.dataset.title = tree.xpath(
        "//h1/text()")[0].strip()
    scraper.dataset.issued = parse(tree.xpath(
        "//span[text() = 'Release date: ']/parent::node()/text()")[1].strip()).date()
    user_requested = tree.xpath(
        "//h2[text() = 'Summary of request']"
    )

    if len(user_requested) > 0:
        scraper.dataset.identifier = tree.xpath(
            "//span[text() = 'Reference number: ']/parent::node()/text()")[1].strip()
        scraper.dataset.comment = tree.xpath(
            "//h2[text() = 'Summary of request']/following-sibling::p/text()")[0].strip()
        distribution_link = tree.xpath(
            "//h2[text()='Download associated with request ']/following-sibling::*/descendant::a")
        if len(distribution_link) > 0:
            distribution = Distribution(scraper)
            distribution.downloadURL = urljoin(scraper.uri, distribution_link[0].get('href'))
            distribution.title = distribution_link[0].text
            distribution_info = distribution_link[0].xpath(
                "following-sibling::text()")
            if len(distribution_info) > 0:
                info_text = distribution_info[0].strip()
                info_re = re.compile(r'\(([0-9\.])+\s+([kMG]B)\s+(xls|ods|pdf)\)')
                info_match = info_re.match(info_text)
                if info_match is not None:
                    size, units, file_type = info_match.groups()
                    if units == 'kB':
                        distribution.byteSize = size * 1024
                    elif units == 'MB':
                        distribution.byteSize = size * 1000000
                    if file_type == 'xls':
                        distribution.mediaType = Excel
                    elif file_type == 'ods':
                        distribution.mediaType = ODS
                    else:
                        distribution.mediaType, encoding = mimetypes.guess_type(distribution.downloadURL)
            scraper.distributions.append(distribution)
    else:
        try:
            scraper.dataset.updateDueOn = parse(tree.xpath(
                "//span[text() = 'Next release: ']/parent::node()/text()")[1].strip()).date()
        except ValueError as e:
            logging.warning('Unexpected "next release" field: ' + str(e))
        except IndexError:
            logging.warning('Unable to find "next release" field')
        try:
            mailto = tree.xpath(
                "//span[text() = 'Contact: ']/following-sibling::a[1]/@href")[0].strip()
            # guard against extraneous, invalid spaces
            scraper.dataset.contactPoint = re.sub(r'^mailto:\s+', 'mailto:', mailto)
        except IndexError:
            logging.warning('Unable to find "contact" field.')
        scraper.dataset.comment = tree.xpath(
            "//h2[text() = 'About this dataset']/following-sibling::p/text()")[0].strip()

        for anchor in tree.xpath("//a[starts-with(@title, 'Download as ')]"):
            distribution = Distribution(scraper)
            distribution.downloadURL = urljoin(scraper.uri, anchor.get('href'))
            type_size_re = re.compile(r'([^(]*)\(([0-9.]+)\s+([^s]+)\)')
            type_size_match = type_size_re.match(anchor.text)
            if type_size_match is not None:
                typ, size, mult = type_size_match.groups()
                if mult == 'kB':
                    distribution.byteSize = float(size) * 1024
                elif mult == 'MB':
                    distribution.byteSize = float(size) * 1000000
                else:
                    distribution.byteSize = float(size)
                if typ.strip() == 'csv':
                    distribution.mediaType = CSV
                elif typ.strip() == 'xlsx':
                    distribution.mediaType = Excel
                elif typ.strip() == 'ods':
                    distribution.mediaType = ODS
                elif typ.strip() == 'structured text':
                    distribution.mediaType = CSDB
                else:
                    distribution.mediaType, encoding = mimetypes.guess_type(distribution.downloadURL)
            distribution.title = scraper.dataset.title
            scraper.distributions.append(distribution)
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
    scraper.dataset.license = tree.xpath(
        "//div[@class='footer-license']//a")[0].get('href')

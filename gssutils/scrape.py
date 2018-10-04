from functools import lru_cache
from io import BytesIO

import messytables
import requests
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import LastModified
from lxml import html
from urllib.parse import urlparse, urljoin
from dateutil.parser import parse
import xypath.loader

from gssutils.metadata import PMDDataset, Distribution
from gssutils.utils import pathify
import re
import html2text
import os
from datetime import datetime


class DistributionFilterError(Exception):
    """ Raised when filters don't uniquely identify a distribution
    """

    def __init__(self, message):
        self.message = message


class Scraper:
    def __init__(self, uri, session=None):
        self.uri = uri
        self.dataset = PMDDataset()
        self.dataset.modified = datetime.now()
        self.distributions = []
        self._dist_filters = []
        self._tableset = None
        self._base_uri = None
        if session:
            self.session = session
        else:
            self.session = CacheControl(requests.Session(),
                                        cache=FileCache('.cache'),
                                        heuristic=LastModified())
        if 'JOB_NAME' in os.environ:
            self.set_base_uri('http://gss-data.org.uk')
            if os.environ['JOB_NAME'].startswith('GSS/'):
                self.set_dataset_id(pathify(os.environ['JOB_NAME'][len('GSS/'):]))
            else:
                self.set_dataset_id(pathify(os.environ['JOB_NAME']))

    @staticmethod
    def to_markdown(node):
        return html2text.html2text(html.tostring(node, encoding='unicode'))

    def run(self):
        page = self.session.get(self.uri)
        tree = html.fromstring(page.text)
        if self.uri.startswith('https://www.ons.gov.uk/'):
            self.dataset.title = tree.xpath(
                "//h1/text()")[0].strip()
            self.dataset.issued = parse(tree.xpath(
                "//span[text() = 'Release date: ']/parent::node()/text()")[1].strip()).date()
            self.dataset.nextUpdateDue = parse(tree.xpath(
                "//span[text() = 'Next release: ']/parent::node()/text()")[1].strip()).date()
            self.dataset.contactPoint = tree.xpath(
                "//span[text() = 'Contact: ']/following-sibling::a[1]/@href")[0].strip()
            self.dataset.description = tree.xpath(
                "//h2[text() = 'About this dataset']/following-sibling::p/text()")[0].strip()
            distribution = Distribution()
            distribution.downloadURL = urljoin(self.uri, tree.xpath(
                "//a[starts-with(@title, 'Download as xls')]/@href")[0].strip())
            distribution.mediaType = 'application/vnd.ms-excel'
            self.distributions.append(distribution)
            self.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
        elif self.uri.startswith('https://www.gov.uk/government/statistics/'):
            date_re = re.compile(r'[0-9]{1,2} (January|February|March|April|May|June|' +
                                 'July|August|September|October|November|December) [0-9]{4}')
            self.dataset.title = tree.xpath("//h1/text()")[0].strip()
            dates = tree.xpath("//div[contains(concat(' ', @class, ' '), 'app-c-published-dates')]/text()")
            if len(dates) > 0 and dates[0].strip().startswith('Published '):
                match = date_re.search(dates[0])
                if match:
                    self.dataset.issued = parse(match.group(0)).date()
            if len(dates) > 1 and dates[1].strip().startswith('Last updated '):
                match = date_re.search(dates[1])
                if match:
                    self.dataset.modified = parse(match.group(0)).date()
            for attachment_section in tree.xpath("//section[contains(concat(' ', @class, ' '), 'attachment')]"):
                distribution = Distribution()
                distribution.downloadURL = urljoin(self.uri, attachment_section.xpath(
                    "div/h2[@class='title']/a/@href")[0].strip())
                distribution.title = attachment_section.xpath("div/h2[@class='title']/a/text()")[0].strip()
                fileExtension = attachment_section.xpath(
                    "div/p[@class='metadata']/span[@class='type']/descendant-or-self::*/text()")[0].strip()
                distribution.mimeType = {
                    'ODS': 'application/vnd.oasis.opendocument.spreadsheet',
                    'XLS': 'application/vnd.ms-excel',
                    'XLSX': 'application/vnd.ms-excel'
                }.get(fileExtension, fileExtension)
                self.distributions.append(distribution)
            next_release_nodes = tree.xpath("//p[starts-with(text(), 'Next release of these statistics:')]/text()")
            if next_release_nodes and (len(next_release_nodes) > 0):
                self.dataset.nextUpdateDue = parse(
                    next_release_nodes[0].strip().split(':')[1].split('.')[0].strip()
                ).date()
            self.dataset.description = Scraper.to_markdown(tree.xpath(
                "//h2[text() = 'Details']/following-sibling::div")[0])
            from_link = tree.xpath(
                "//span[contains(concat(' ', @class, ' '), 'app-c-publisher-metadata__definition_sentence')]/a/@href")
            if len(from_link) > 0:
                self.dataset.publisher = urljoin(self.uri, from_link[0])
        else:
            raise NotImplementedError(f'No scraper for {self.uri}')
        return self

    def dist_filter(self, **kwargs):
        for k, v in kwargs.items():
            self._dist_filters.append(lambda x: x.__dict__[k] == v)

    @property
    def the_distribution(self):
        if len(self._dist_filters) > 0:
            dists = [dist for dist in self.distributions if all(
                [f(dist) for f in self._dist_filters])]
            if len(dists) > 1:
                raise DistributionFilterError('more than one distribution matches given filter(s)')
            elif len(dists) == 0:
                raise DistributionFilterError('no distributions match given filter(s)')
            else:
                return dists[0]
        if len(self.distributions) == 1:
            return self.distributions[0]
        elif len(self.distributions) > 1:
            raise DistributionFilterError('more than one distribution, but no filters given.')
        else:
            raise DistributionFilterError('no distributions.')

    @property
    def data_uri(self):
        return self.the_distribution.downloadURL

    @lru_cache(maxsize=2)
    def _get_databaker_excel(self, url):
        # monkeypatches from databaker
        from databaker import overrides
        fobj = BytesIO(self.session.get(url).content)
        tableset = messytables.excel.XLSTableSet(fobj)
        tabs = list(xypath.loader.get_sheets(tableset, "*"))
        return tabs

    @property
    def as_databaker(self):
        dist = self.the_distribution
        if dist.mediaType == 'application/vnd.ms-excel':
            return self._get_databaker_excel(dist.downloadURL)

    def set_base_uri(self, uri):
        self._base_uri = uri
        self.dataset.sparqlEndpoint = urljoin(uri, '/sparql')

    def set_dataset_id(self, id):
        self.dataset.set_uri(urljoin(self._base_uri, f'data/{id}'))
        self.dataset.set_graph(urljoin(self._base_uri, f'graph/{id}/metadata'))
        self.dataset.inGraph = urljoin(self._base_uri, f'graph/{id}')

    def set_family(self, family):
        self.dataset.family = family

    def generate_trig(self):
        return self.dataset.as_quads().serialize(format='trig')

    @property
    def title(self):
        return self.dataset.title

    @property
    def description(self):
        return self.dataset.description

    @property
    def publication_date(self):
        return self.dataset.issued.isoformat()

    @property
    def next_release(self):
        return self.dataset.nextUpdateDue.isoformat()

    @property
    def contact(self):
        return self.dataset.contactPoint

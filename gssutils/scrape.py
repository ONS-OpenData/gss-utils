import os
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from urllib.parse import urljoin

import html2text
import messytables
import requests
import xypath.loader
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import LastModified
from lxml import html

import gssutils.scrapers
from gssutils.metadata import PMDDataset
from gssutils.utils import pathify


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
        if type(node) == list:
            return html2text.html2text('\n'.join([html.tostring(n, encoding='unicode') for n in node]))
        else:
            return html2text.html2text(html.tostring(node, encoding='unicode'))

    def run(self):
        page = self.session.get(self.uri)
        tree = html.fromstring(page.text)
        scraped = False
        for start_uri, scrape in gssutils.scrapers.scraper_list:
            if self.uri.startswith(start_uri):
                scrape(self, tree)
                scraped = True
                break
        if not scraped:
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

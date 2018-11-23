import logging
import os
from datetime import datetime
from urllib.parse import urljoin

import html2text
import requests
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import LastModified
from lxml import html

import gssutils.scrapers
from gssutils.metadata import PMDDataset, Excel, ODS, Catalog
from gssutils.utils import pathify


class DistributionFilterError(Exception):
    """ Raised when filters don't uniquely identify a distribution
    """

    def __init__(self, message):
        self.message = message


class Scraper:
    def __init__(self, uri, session=None):
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
        self.uri = uri
        self.datasets = []
        self.dataset = PMDDataset()
        self.catalog = Catalog()
        self.dataset.modified = datetime.now()
        self.distributions = []
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

        self._run()

    def _repr_markdown_(self):
        md = ""
        if hasattr(self.dataset, 'label'):
            md = md + f'## {self.dataset.label}\n\n'
        if hasattr(self.dataset, 'comment'):
            md = md + f'{self.dataset.comment}\n\n'
        if hasattr(self.dataset, 'description'):
            md = md + f'### Description\n\n{self.dataset.description}\n\n'
        if len(self.distributions) > 0:
            md = md + "### Distributions\n\n"
            for d in self.distributions:
                t = {Excel: 'MS Excel Spreadsheet', ODS: 'ODF Spreadsheet'}
                md = md + f"1. {d.title} ([{t.get(d.mediaType, d.mediaType)}]({d.downloadURL}))\n"
        return md

    @staticmethod
    def to_markdown(node):
        if type(node) == list:
            return html2text.html2text('\n'.join([html.tostring(n, encoding='unicode') for n in node]))
        else:
            return html2text.html2text(html.tostring(node, encoding='unicode'))

    def _run(self):
        page = self.session.get(self.uri)
        tree = html.fromstring(page.text)
        scraped = False
        for start_uri, scrape in gssutils.scrapers.scraper_list:
            if self.uri.startswith(start_uri):
                self.dataset.landingPage = self.uri
                scrape(self, tree)
                scraped = True
                break
        if not scraped:
            raise NotImplementedError(f'No scraper for {self.uri}')
        return self

    def distribution(self, **kwargs):
        matching_dists = [
            dist for dist in self.distributions if all(
                [v(dist.__dict__[k]) if callable(v) else dist.__dict__[k] == v
                 for k, v in kwargs.items()]
            )]
        if len(matching_dists) > 1:
            raise DistributionFilterError('more than one distribution matches given filter(s)')
        elif len(matching_dists) == 0:
            raise DistributionFilterError('no distributions match given filter(s)')
        else:
            return matching_dists[0]

    def set_base_uri(self, uri):
        self._base_uri = uri
        self.dataset.sparqlEndpoint = urljoin(uri, '/sparql')

    def set_dataset_id(self, id):
        self.dataset.set_uri(urljoin(self._base_uri, f'data/{id}'))
        self.dataset.set_graph(urljoin(self._base_uri, f'graph/{id}/metadata'))
        self.dataset.inGraph = urljoin(self._base_uri, f'graph/{id}')

    def set_family(self, family):
        self.dataset.family = family

    def set_theme(self, theme):
        self.dataset.theme = theme

    def set_description(self, description):
        self.dataset.description = description

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

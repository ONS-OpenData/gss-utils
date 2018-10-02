import requests
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import LastModified
from lxml import html
from urllib.parse import urlparse, urljoin
from dateutil.parser import parse


class Scraper:
    def __init__(self, uri):
        self.uri = uri
        self.session = CacheControl(requests.Session(),
                                    cache=FileCache('.cache'),
                                    heuristic=LastModified())

    def run(self):
        page = self.session.get(self.uri)
        tree = html.fromstring(page.text)
        self._md = {
            'title': tree.xpath("//h1/text()")[0].strip(),
            'releaseDate': parse(tree.xpath("//span[text() = 'Release date: ']/parent::node()/text()")[1].strip()).date(),
            'nextRelease': parse(tree.xpath("//span[text() = 'Next release: ']/parent::node()/text()")[1].strip()).date(),
            'mailto': tree.xpath("//span[text() = 'Contact: ']/following-sibling::a[1]/@href")[0].strip(),
            'fileURL': urljoin(self.uri, tree.xpath("//a[starts-with(@title, 'Download as xls')]/@href")[0].strip()),
            'about': tree.xpath("//h2[text() = 'About this dataset']/following-sibling::p/text()")[0].strip()
        }

    @property
    def data_uri(self):
        return self._md['fileURL']

    @property
    def title(self):
        return self._md['title']

    @property
    def description(self):
        return self._md['about']

    @property
    def publication_date(self):
        return self._md['releaseDate'].isoformat()

    @property
    def next_release(self):
        return self._md['nextRelease'].isoformat()

    @property
    def contact(self):
        return self._md['mailto']
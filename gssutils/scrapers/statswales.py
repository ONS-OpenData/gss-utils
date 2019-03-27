from io import StringIO

import rdflib
from dateutil.parser import parse
from rdflib import RDF, URIRef
from rdflib.namespace import DCTERMS

from gssutils.metadata import DCAT, Distribution, GOV


def scrape(scraper, tree):
    pageGraph = rdflib.Graph()
    page = StringIO(scraper.session.get(scraper.uri).text)
    pageGraph.parse(page, format="html")
    dataset = pageGraph.value(predicate=RDF.type, object=DCAT.Dataset, any=False)
    scraper.dataset.title = pageGraph.value(dataset, DCTERMS.title).value.strip()
    scraper.dataset.comment = pageGraph.value(dataset, DCTERMS.description).value.strip()
    license = str(pageGraph.value(dataset, DCTERMS.license))
    if license == 'http://www.nationalarchives.gov.uk/doc/open-government-licence':
        scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
    else:
        scraper.dataset.license = license
    publisher = pageGraph.value(dataset, DCTERMS.publisher)
    if publisher == URIRef('http://www.gov.wales/'):
        scraper.dataset.publisher = GOV['welsh-government']
    else:
        scraper.dataset.publisher = publisher
    scraper.dataset.issued = parse(pageGraph.value(dataset, DCTERMS.created)).date()
    scraper.dataset.modified = parse(pageGraph.value(dataset, DCTERMS.modified)).date()
    for pageDist in pageGraph.subjects(RDF.type, DCAT.Distribution):
        dist = Distribution(scraper)
        dist.title = pageGraph.value(pageDist, DCTERMS.title).value.strip()
        dist.downloadURL = str(pageGraph.value(pageDist, DCAT.accessURL))
        dist.mediaType = pageGraph.value(pageDist, DCAT.mediaType).value.strip()
        scraper.distributions.append(dist)


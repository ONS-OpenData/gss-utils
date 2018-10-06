from enum import Enum
from io import BytesIO
import xypath.loader
import pandas as pd

import messytables
from rdflib import Dataset as Quads, Literal, URIRef, Graph, BNode
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, Namespace, NamespaceManager, VOID
from inspect import getmro
import html

DCAT = Namespace('http://www.w3.org/ns/dcat#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
PMD = Namespace('http://publishmydata.com/def/dataset#')
GOV = Namespace('https://www.gov.uk/government/organisations/')
QB = Namespace('http://purl.org/linked-data/cube#')
GDP = Namespace(f'http://gss-data.org.uk/def/gdp#')
OGL_3 = URIRef('http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/')

namespaces = NamespaceManager(Graph())
namespaces.bind('dcat', DCAT)
namespaces.bind('pmd', PMD)
namespaces.bind('spdx', SPDX)
namespaces.bind('rdf', RDF)
namespaces.bind('rdfs', RDFS)
namespaces.bind('xsd', XSD)
namespaces.bind('gov', GOV)
namespaces.bind('gdp', GDP)
namespaces.bind('qb', QB)
namespaces.bind('void', VOID)
namespaces.bind('dct', DCTERMS)


class Status(Enum):
    mandatory = 1
    recommended = 2


class Metadata:

    _properties_metadata = {
        'label': (RDFS.label, Status.mandatory, lambda s: Literal(s, 'en')),
        'comment': (RDFS.comment, Status.mandatory, lambda s: Literal(s, 'en'))
    }

    def __init__(self):
        self.uri = BNode()
        self.graph = BNode()

    def __setattr__(self, name, value):
        if name in self._properties_metadata:
            self.__dict__[name] = value
        else:
            super().__setattr__(name, value)

    def get_property(self, p):
        obs = []
        for k in self._properties_metadata:
            prop, status, f = self._properties_metadata[k]
            if prop == p:
                obs.append(f(self.__dict__[k]))
        if len(obs) == 0:
            return None
        elif len(obs) == 1:
            return obs[0]
        else:
            return obs

    def set_uri(self, uri):
        self.uri = URIRef(uri)

    def set_graph(self, uri):
        self.graph = URIRef(uri)

    def as_quads(self):
        quads = Quads()
        quads.namespace_manager = namespaces
        graph = quads.graph(self.graph)
        for c in getmro(type(self)):
            if hasattr(c, '_type'):
                if type(c._type) == tuple:
                    for t in c._type:
                        graph.add((self.uri, RDF.type, t))
                else:
                    graph.add((self.uri, RDF.type, c._type))
        for local_name, profile in self._properties_metadata.items():
            if local_name in self.__dict__:
                prop, status, f = profile
                graph.add((self.uri, prop, f(self.__dict__[local_name])))
        return quads

    def _repr_html_(self):
        s = f'<h3>{type(self).__name__}</h3>\n<dl>'
        for local_name, profile in self._properties_metadata.items():
            if local_name in self.__dict__:
                prop, status, f = profile
                s = s + f'<dt>{html.escape(prop.n3(namespaces))}</dt>'
                term = f(self.__dict__[local_name])
                if type(term) == URIRef:
                    s = s + f'<dd><a href={str(term)}>{html.escape(term.n3())}</a></dd>\n'
                else:
                    s = s + f'<dd>{html.escape(term.n3())}</dd>\n'
        s = s + '</dl>'
        return s


class Dataset(Metadata):

    _type = DCAT.Dataset
    _properties_metadata = dict(Metadata._properties_metadata)
    _properties_metadata.update({
        'title': (DCTERMS.title, Status.mandatory, lambda s: Literal(s, 'en')),
        'description': (DCTERMS.description, Status.mandatory, lambda s: Literal(s, 'en')),
        'publisher': (DCTERMS.publisher, Status.mandatory, lambda s: URIRef(s)),
        'issued': (DCTERMS.issued, Status.mandatory, lambda d: Literal(d)), # date/time
        'modified': (DCTERMS.modified, Status.recommended, lambda d: Literal(d)),
        'identifier': (DCTERMS.identifier, Status.mandatory, lambda s: Literal(s)),
        'keyword': (DCAT.keyword, Status.mandatory, lambda s: Literal(s, 'en')),
        'language': (DCTERMS.language, Status.mandatory, lambda s: Literal(s)),
        'contactPoint': (DCAT.contactPoint, Status.mandatory, lambda s: URIRef(s)), # Should be vcard:Kind
        'temporal': (DCTERMS.temporal, Status.mandatory, lambda s: URIRef(s)),
        'spatial': (DCTERMS.spatial, Status.mandatory, lambda s: URIRef(s)),
        'accrualPeriodicity': (DCTERMS.accrualPeriodicity, Status.mandatory, lambda s: URIRef(s)), # dct:Frequency
        'landingPage': (DCAT.landingPage, Status.mandatory, lambda s: URIRef(s)), # foaf:Document
        'theme': (DCAT.theme, Status.mandatory, lambda s: URIRef(s)), # skos:Concept
        'distribution': (DCAT.distribution, Status.mandatory, lambda s: URIRef(s))
    })


class QBDataSet(Dataset):

    _type = QB.DataSet


class PMDDataset(QBDataSet):

    _type = (PMD.LinkedDataset, PMD.Dataset)
    _properties_metadata = dict(QBDataSet._properties_metadata)
    _properties_metadata.update({
        'nextUpdateDue': (PMD.nextUpdateDue, Status.recommended, lambda d: Literal(d)),  # date/time
        'family': (GDP.family, Status.recommended, lambda f: GDP[f.lower()]),
        'sparqlEndpoint': (VOID.sparqlEndpoint, Status.recommended, lambda s: URIRef(s)),
        'inGraph': (PMD.graph, Status.mandatory, lambda s: URIRef(s)),
        'contactEmail': (PMD.contactEmail, Status.recommended, lambda s: URIRef(s)),
        'license': (DCTERMS.license, Status.recommended, lambda s: URIRef(s)),
        'creator': (DCTERMS.creator, Status.recommended, lambda s: URIRef(s))
    })

    def __setattr__(self, key, value):
        if key == 'title':
            self.label = value
        elif key == 'description':
            self.comment = value
        elif key == 'contactPoint' and value.startswith('mailto:'):
            self.contactEmail = value
        elif key == 'publisher':
            self.creator = value
        super().__setattr__(key, value)


class FormatError(Exception):
    """ Raised when the available file format can't be used
    """

    def __init__(self, message):
        self.message = message


class Distribution(Metadata):

    _type = DCAT.Distribution
    _properties_metadata = dict(Metadata._properties_metadata)
    _properties_metadata.update({
        'title': (DCTERMS.title, Status.mandatory, lambda s: Literal(s, 'en')),
        'description': (DCTERMS.description, Status.mandatory, lambda s: Literal(s, 'en')),
        'issued': (DCTERMS.issued, Status.mandatory, lambda d: Literal(d)),
        'modified': (DCTERMS.modified, Status.recommended, lambda d: Literal(d)),
        'license': (DCTERMS.license, Status.mandatory, lambda s: URIRef(s)),
        'rights': (DCTERMS.rights, Status.mandatory, lambda s: Literal(s, 'en')),
        'accessURL': (DCAT.accessURL, Status.mandatory, lambda u: URIRef(u)),
        'downloadURL': (DCAT.downloadURL, Status.mandatory, lambda u: URIRef(u)),
        'mediaType': (DCAT.mediaType, Status.mandatory, lambda s: Literal(s)),
        'format': (DCTERMS.format, Status.recommended, lambda s: Literal(s)),
        'byteSize': (DCAT.byteSize, Status.recommended, lambda i: Literal(i)),
        'checksum': (SPDX.checksum, Status.recommended, lambda i: Literal(i)),
        'language': (DCTERMS.language, Status.mandatory, lambda s: Literal(s))
    })

    def __init__(self, scraper):
        super().__init__()
        self.session = scraper.session

    def as_databaker(self, **kwargs):
        if self.mediaType == 'application/vnd.ms-excel':
            fobj = BytesIO(self.session.get(self.downloadURL).content)
            tableset = messytables.excel.XLSTableSet(fobj)
            tabs = list(xypath.loader.get_sheets(tableset, "*"))
            return tabs
        raise FormatError('Databaker requires Excel spreadsheets.')

    def as_pandas(self, **kwargs):
        if self.mediaType == 'application/vnd.ms-excel':
            fobj = BytesIO(self.session.get(self.downloadURL).content)
            return pd.read_excel(fobj, **kwargs)

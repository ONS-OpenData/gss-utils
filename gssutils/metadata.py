from enum import Enum
from rdflib import Dataset, Literal, URIRef, Graph
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, Namespace, NamespaceManager
import messytables

DCAT = Namespace('http://www.w3.org/ns/dcat#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
PMD = Namespace('http://publishmydata.com/def/dataset#')
GOV = Namespace('https://www.gov.uk/government/organisations/')
namespaces = NamespaceManager(Graph())
namespaces.bind('dcat', DCAT)
namespaces.bind('pmd', PMD)
namespaces.bind('spdx', SPDX)
namespaces.bind('rdf', RDF)
namespaces.bind('rdfs', RDFS)
namespaces.bind('xsd', XSD)
namespaces.bind('gov', GOV)


class Metadata:

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

    def asTrig(self):
        quads = Dataset()
        return ""

    def _repr_html_(self):
        s = f'<b>{type(self).__name__}</b>:\n<dl>\n'
        for k, v in self.__dict__.items():
            s = s + f'<dt>{k}</dt><dd>{v}</dd>\n'
        s = s + '</dl>'
        return s


class Status(Enum):
    mandatory = 1
    recommended = 2


class Dataset(Metadata):

    _properties_metadata = {
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
        'distribution': (DCAT.distribution, Status.mandatory, lambda s: URIRef(s)),
        'nextUpdateDue': (PMD.nextUpdateDue, Status.recommended, lambda d: Literal(d)) # date/time
    }


class Distribution(Metadata):

    _properties_metadata = {
        'title': (DCTERMS.title, Status.mandatory),
        'description': (DCTERMS.description, Status.mandatory),
        'issued': (DCTERMS.issued, Status.mandatory),
        'modified': (DCTERMS.modified, Status.recommended),
        'license': (DCTERMS.license, Status.mandatory),
        'rights': (DCTERMS.rights, Status.mandatory),
        'accessURL': (DCAT.accessURL, Status.mandatory),
        'downloadURL': (DCAT.downloadURL, Status.mandatory),
        'mediaType': (DCAT.mediaType, Status.mandatory),
        'format': (DCTERMS.format, Status.recommended),
        'byteSize': (DCAT.byteSize, Status.recommended),
        'checksum': (SPDX.checksum, Status.recommended),
        'language': (DCTERMS.language, Status.mandatory)
    }

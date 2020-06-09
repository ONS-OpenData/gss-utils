from rdflib import URIRef, Graph
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, Namespace, NamespaceManager, VOID

namespaces = NamespaceManager(Graph())

DCAT = Namespace('http://www.w3.org/ns/dcat#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
PMD = Namespace('http://publishmydata.com/def/dataset#')
PMDCAT = Namespace('http://publishmydata.com/pmdcat#')
GOV = Namespace('https://www.gov.uk/government/organisations/')
QB = Namespace('http://purl.org/linked-data/cube#')
GDP = Namespace(f'http://gss-data.org.uk/def/gdp#')
THEME = Namespace('http://gss-data.org.uk/def/concept/statistics-authority-themes/')
PROV = Namespace('http://www.w3.org/ns/prov#')
ODRL = Namespace('http://www.w3.org/ns/odrl/2/')

OGL_3 = URIRef('http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/')
MARKDOWN = URIRef('https://www.w3.org/ns/iana/media-types/text/markdown#Resource')

namespaces.bind('dcat', DCAT)
namespaces.bind('pmd', PMD)
namespaces.bind('spdx', SPDX)
namespaces.bind('rdf', RDF)
namespaces.bind('rdfs', RDFS)
namespaces.bind('xsd', XSD)
namespaces.bind('gov', GOV)
namespaces.bind('gdp', GDP)
namespaces.bind('theme', THEME)
namespaces.bind('qb', QB)
namespaces.bind('void', VOID)
namespaces.bind('dct', DCTERMS)
namespaces.bind('pmdcat', PMDCAT)
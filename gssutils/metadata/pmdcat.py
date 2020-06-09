from datetime import datetime, timezone

from rdflib import URIRef, Literal
from rdflib.namespace import VOID, DCTERMS

from gssutils.metadata import PMDCAT, DCAT, MARKDOWN, PMD, GDP
from gssutils.metadata.base import Status
from gssutils.metadata.dcat import Dataset as DCATDataset


class Dataset(DCATDataset):

    _type = (PMDCAT.Dataset, DCAT.Dataset)
    _properties_metadata = dict(DCATDataset._properties_metadata)
    _properties_metadata.update({
        'metadataGraph': (PMDCAT.metadataGraph, Status.mandatory, lambda s: URIRef(s)),
        'graph': (PMDCAT.graph, Status.mandatory, lambda s: URIRef(s)),
        'datasetContents': (PMDCAT.datasetContents, Status.mandatory, lambda s: URIRef(s)),
        'markdownDescription': (PMDCAT.markdownDescription, Status.recommended, lambda l: Literal(l, MARKDOWN)),
        'dependsOn': (PMDCAT.dependsOn, Status.recommended, lambda ds: URIRef(ds.uri)),

        'updateDueOn': (PMD.updateDueOn, Status.recommended, lambda d: Literal(d)),  # date/time
        'family': (GDP.family, Status.recommended, lambda f: GDP[f.lower()]),
        'sparqlEndpoint': (VOID.sparqlEndpoint, Status.recommended, lambda s: URIRef(s)),
        'inGraph': (PMD.graph, Status.mandatory, lambda s: URIRef(s)),
        'contactEmail': (PMD.contactEmail, Status.recommended, lambda s: URIRef(s)),
        'license': (DCTERMS.license, Status.mandatory, lambda s: URIRef(s)),
        'creator': (DCTERMS.creator, Status.recommended, lambda s: URIRef(s)),
    })

    def __init__(self, landingPage):
        super().__init__()
        self.landingPage = landingPage

    def __setattr__(self, key, value):
        if key == 'title':
            self.label = value
        elif key == 'contactPoint' and value.startswith('mailto:'):
            self.contactEmail = value
        elif key == 'publisher':
            self.creator = value
        elif key == 'modified':
            # TODO: remove the following once we distinguish between the modification datetime of a dataset
            #       in PMD and the last modification datetime of the dataset by the publisher.
            value = datetime.now(timezone.utc).astimezone()
        super().__setattr__(key, value)
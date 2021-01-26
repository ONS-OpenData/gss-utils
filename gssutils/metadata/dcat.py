import json
from io import BytesIO

import datetime
import messytables
import pandas as pd
import pyexcel
import xypath.loader
import os
import logging
import requests

import backoff
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import URIRef, Literal, XSD
from rdflib.namespace import DCTERMS, FOAF
from pathlib import Path

from gssutils.metadata import DCAT, PROV, ODRL, SPDX
from gssutils.metadata.base import Metadata, Status
from gssutils.metadata.mimetype import ExcelTypes, ODS
from gssutils.transform.download import construct_odata_dataframe, get_simple_csv_pandas, get_simple_databaker_tabs
from gssutils.utils import pathify


class Resource(Metadata):
    _type = DCAT.Resource
    _properties_metadata = dict(Metadata._properties_metadata)
    _properties_metadata.update({
        'accessRights': (DCTERMS.accessRights, Status.recommended, URIRef),
        'contactPoint': (DCAT.contactPoint, Status.recommended, URIRef),  # Todo: VCARD
        'creator': (DCTERMS.creator, Status.recommended, URIRef),
        'description': (DCTERMS.description, Status.recommended, lambda s: Literal(s, 'en')),
        'title': (DCTERMS.title, Status.recommended, lambda s: Literal(s, 'en')),
        'issued': (DCTERMS.issued, Status.recommended, Literal),  # date/time
        'modified': (DCTERMS.modified, Status.recommended, Literal),
        'language': (DCTERMS.language, Status.recommended, Literal),
        'publisher': (DCTERMS.publisher, Status.recommended, URIRef),
        'identifier': (DCTERMS.identifier, Status.recommended, Literal),
        'theme': (DCAT.theme, Status.recommended, URIRef),  # skos:Concept
        'type': (DCTERMS.type, Status.recommended, URIRef),  # skos:Concept
        'relation': (DCTERMS.relation, Status.recommended, URIRef),
        'qualifiedRelation': (DCAT.qualifiedRelation, Status.recommended, URIRef),
        'keyword': (DCAT.keyword, Status.recommended, lambda l: Literal(l, 'en')),
        'landingPage': (DCAT.landingPage, Status.mandatory, URIRef),  # foaf:Document
        'qualifiedAttribution': (PROV.qualifiedAttribution, Status.recommended, URIRef),
        'license': (DCTERMS.license, Status.recommended, URIRef),
        'rights': (DCTERMS.rights, Status.recommended, URIRef),
        'hasPolicy': (ODRL.hasPolicy, Status.recommended, URIRef),
        'isReferencedBy': (DCTERMS.isReferencedBy, Status.recommended, URIRef)
    })


class Dataset(Resource):
    _type = DCAT.Dataset
    _properties_metadata = dict(Resource._properties_metadata)
    _properties_metadata.update({
        'distribution': (DCAT.distribution, Status.mandatory, lambda d: URIRef(d.uri)),
        'accrualPeriodicity': (DCTERMS.accrualPeriodicity, Status.mandatory, URIRef),  # dct:Frequency
        'spatial': (DCTERMS.spatial, Status.mandatory, URIRef),
        'spatialResolutionInMeters': (DCAT.spatialResolutionInMeters, Status.optional, lambda l: Literal(l, XSD.decimal)),
        'temporal': (DCTERMS.temporal, Status.mandatory, URIRef),
        'temporalResolution': (DCAT.temporalResolution, Status.optional, lambda l: Literal(l, XSD.duration)),
        'wasGeneratedBy': (PROV.wasGeneratedBy, Status.optional, URIRef)
    })

    def __setattr__(self, key, value):
        if key == 'distribution':
            if type(value) == list:
                for d in value:
                    d._graph = self._graph
            else:
                value._graph = self._graph
        super().__setattr__(key, value)


class Catalog(Dataset):
    _type = DCAT.Catalog
    _properties_metadata = dict(Dataset._properties_metadata)
    _properties_metadata.update({
        'homepage': (FOAF.homepage, Status.recommended, URIRef),
        'themeTaxonomy': (DCAT.themeTaxonomy, Status.optional, URIRef),
        'hasPart': (DCTERMS.hasPart, Status.optional, URIRef),
        'dataset': (DCAT.dataset, Status.recommended, URIRef),
        'service': (DCAT.service, Status.recommended, URIRef),
        'catalog': (DCAT.catalog, Status.optional, URIRef),
        'record': (DCAT.record, Status.recommended, lambda r: URIRef(r.uri))
    })


class CatalogRecord(Metadata):
    _type = DCAT.Catalog
    _properties_metadata = dict(Metadata._properties_metadata)
    _properties_metadata.update({
        'title': (DCTERMS.title, Status.mandatory, lambda s: Literal(s, 'en')),
        'description': (DCTERMS.description, Status.mandatory, lambda s: Literal(s, 'en')),
        'issued': (DCTERMS.issued, Status.mandatory, lambda d: Literal(d)),
        'modified': (DCTERMS.modified, Status.recommended, lambda d: Literal(d)),
        'primaryTopic': (FOAF.primaryTopic, Status.mandatory, lambda s: URIRef(s.uri)),
        'conformsTo': (DCTERMS.conformsTo, Status.recommended, lambda s: URIRef(s))
    })


class Distribution(Metadata):

    _core_properties = Metadata._core_properties + ['_session']
    _type = DCAT.Distribution
    _properties_metadata = dict(Metadata._properties_metadata)
    _properties_metadata.update({
        'title': (DCTERMS.title, Status.mandatory, lambda s: Literal(s, 'en')),
        'description': (DCTERMS.description, Status.mandatory, lambda s: Literal(s, 'en')),
        'issued': (DCTERMS.issued, Status.mandatory, lambda d: Literal(d)),
        'modified': (DCTERMS.modified, Status.recommended, lambda d: Literal(d)),
        'license': (DCTERMS.license, Status.mandatory, lambda s: URIRef(s)),
        'accessRights': (DCTERMS.rights, Status.recommended, URIRef),
        'rights': (DCTERMS.rights, Status.mandatory, URIRef),
        'hasPolicy': (ODRL.hasPolicy, Status.optional, URIRef),
        'accessURL': (DCAT.accessURL, Status.mandatory, URIRef),
        'accessService': (DCAT.accessService, Status.optional, URIRef),
        'downloadURL': (DCAT.downloadURL, Status.mandatory, lambda u: URIRef(u)),
        'byteSize': (DCAT.byteSize, Status.recommended, lambda i: Literal(i)),
        'spatialResolutionInMeters': (DCAT.spatialResolutionInMeters, Status.optional, lambda d: Literal(d, XSD.decimal)),
        'temporalResolution': (DCAT.temporalResolution, Status.optional, lambda l: Literal(l, XSD.duration)),
        'conformsTo': (DCTERMS.conformsTo, Status.recommended, URIRef),
        'mediaType': (DCAT.mediaType, Status.mandatory, lambda s: Literal(s)),
        'format': (DCTERMS.format, Status.recommended, lambda s: Literal(s)),
        'compressFormat': (DCAT.compressFormat, Status.recommended, Literal),
        'packageFormat': (DCAT.packageFormat, Status.optional, Literal)
    })

    def __init__(self, scraper):
        super().__init__()
        self._session = scraper.session
        self._seed = scraper.seed

    def __setattr__(self, key, value):
        if key == 'downloadURL':
            self._uri = URIRef(value)
        super().__setattr__(key, value)

    def open(self):
        stream = self._session.get(self.downloadURL, stream=True).raw
        stream.decode_content = True
        return stream

    def as_databaker(self, **kwargs):
        return get_simple_databaker_tabs(self, **kwargs)

    def as_pandas(self, **kwargs):

        if "odataConversion" in self._seed.keys():
            return construct_odata_dataframe(self, **kwargs)
            
        return get_simple_csv_pandas(self, **kwargs)
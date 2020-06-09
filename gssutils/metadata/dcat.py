import json
from io import BytesIO

import messytables
import pandas as pd
import pyexcel
import xypath.loader
from rdflib import URIRef, Literal, XSD
from rdflib.namespace import DCTERMS, FOAF

from gssutils.metadata import DCAT, PROV, ODRL, SPDX
from gssutils.metadata.base import Metadata, Status
from gssutils.metadata.mimetype import ExcelTypes, ODS


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
        self.session = scraper.session

    def open(self):
        stream = self.session.get(self.downloadURL, stream=True).raw
        stream.decode_content = True
        return stream

    def as_databaker(self, **kwargs):
        if self.mediaType in ExcelTypes:
            with self.open() as fobj:
                tableset = messytables.excel.XLSTableSet(fileobj=fobj)
                tabs = list(xypath.loader.get_sheets(tableset, "*"))
                return tabs
        elif self.mediaType == ODS:
            with self.open() as ods_obj:
                excel_obj = BytesIO()
                book = pyexcel.get_book(file_type='ods', file_content=ods_obj, library='pyexcel-ods3')
                book.save_to_memory(file_type='xls', stream=excel_obj)
                tableset = messytables.excel.XLSTableSet(fileobj=excel_obj)
                tabs = list(xypath.loader.get_sheets(tableset, "*"))
                return tabs
        raise FormatError(f'Unable to load {self.mediaType} into Databaker.')

    def as_pandas(self, **kwargs):
        if self.mediaType in ExcelTypes:
            with self.open() as fobj:
                # pandas 0.25 now tries to seek(0), so we need to read and buffer the stream
                buffered_fobj = BytesIO(fobj.read())
                return pd.read_excel(buffered_fobj, **kwargs)
        elif self.mediaType == ODS:
            with self.open() as ods_obj:
                if 'sheet_name' in kwargs:
                    return pd.DataFrame(pyexcel.get_array(file_content=ods_obj,
                                                          file_type='ods',
                                                          library='pyexcel-ods3',
                                                          **kwargs))
                else:
                    book = pyexcel.get_book(file_content=ods_obj,
                                            file_type='ods',
                                            library='pyexcel-ods3')
                    return {sheet.name: pd.DataFrame(sheet.get_array(**kwargs)) for sheet in book}
        elif self.mediaType == 'text/csv':
            with self.open() as csv_obj:
                return pd.read_csv(csv_obj, **kwargs)
        elif self.mediaType == 'application/json':
            # Assume odata
            to_fetch = self.downloadURL
            tables = []
            while to_fetch is not None:
                data = self.session.get(to_fetch).json()
                tables.append(pd.read_json(json.dumps(data['value']), orient='records'))
                if 'odata.nextLink' in data and data['odata.nextLink'] != '':
                    to_fetch = data['odata.nextLink']
                else:
                    to_fetch = None
            return pd.concat(tables, ignore_index=True)
        raise FormatError(f'Unable to load {self.mediaType} into Pandas DataFrame.')
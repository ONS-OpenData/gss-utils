import json
from io import BytesIO

import datetime
import messytables
import pandas as pd
import pyexcel
import xypath.loader
import os
import logging

from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import URIRef, Literal, XSD
from rdflib.namespace import DCTERMS, FOAF
from pathlib import Path

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


class FormatError(Exception):
    """ Raised when the available file format can't be used
    """

    def __init__(self, message):
        self.message = message


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
        self._info = scraper.info

    def __setattr__(self, key, value):
        if key == 'downloadURL':
            self._uri = URIRef(value)
        super().__setattr__(key, value)

    def open(self):
        stream = self._session.get(self.downloadURL, stream=True).raw
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

        if "uktradeinfo.com" in self.downloadURL:
            return construct_uktradeinfo_dataframe(self)

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
                data = self._session.get(to_fetch).json()
                tables.append(pd.read_json(json.dumps(data['value']), orient='records'))
                if 'odata.nextLink' in data and data['odata.nextLink'] != '':
                    to_fetch = data['odata.nextLink']
                else:
                    to_fetch = None
            return pd.concat(tables, ignore_index=True)
        raise FormatError(f'Unable to load {self.mediaType} into Pandas DataFrame.')


def find_missing_periods(odata_api_periods: list, pmd_periods: list) -> list:
    """
    Given two lists, one of periods from the odata api, another of periods
    from pmd. Return items that are on the api but not pmd.
    """
    
    # TODO - this function! returning everything for now
    return odata_api_periods


def get_principle_dataframe(distro: Distribution, periods_wanted: list):
    """
    Given a distribution object and a list of periods of data we want
    return a dataframe
    """
    url = distro.downloadURL

    return _get_odata_data(url) # TODO - dont forget we're returning a blank dataframe here!


def get_supplimentary_dataframes(distro: Distribution) -> dict:
    """
    Supplement the base datframe with expand and foreign deifnition calls etc
    """

    sup = distro.info['odatConversion']['supplementalEndpoints']

    for name, url in sup, sup['endpoint']:
        
        pass

    # TODO - everything :)
    return {'key', pd.DataFrame}

def _get_odata_data(url) -> pd.DataFrame():
    return pd.DataFrame()

def construct_uktradeinfo_dataframe(distro: Distribution, periods_wanted: list = None):
    """
    Construct a dataframe via a series of api calls.
    """

    # Unless periods have been explicitly requested, use PMD and the odataAPI to
    # work out what periods of data we want
    if periods_wanted is None:
        pmd_periods = get_pmd_periods(distro)
        odata_api_periods = get_odata_api_periods(distro)
        periods_wanted = find_missing_periods(odata_api_periods, pmd_periods)

    # use those periods to construct the principle dataframe
    df = get_principle_dataframe(distro.downloadURL, periods_wanted)

    # expand this dataframe with supplementary data
    df = get_supplimentary_dataframes(distro)

    return df

def get_pmd_periods(distro: Distribution) -> list:
    """
    Given the downloadURL from the scraper, return a list of periods from pmd4
    note - when testing with a seed, url here will be the dataURL from the info.json
    """

    dataset = Path(os.path.dirname(os.path.abspath(__file__))).parent.split()[-1]
    family = distro.info['families'][0]
    # Assumption that no cases of multiple datasets from a single API endpoint, so...

    dataset_url = f'http://gss-data.org.uk/data/gss_data/{family}/{dataset}#dataset'
    endpoint_url = distro.info['odataConversion']['publishedLocation']

    logging.info('Dataset url is {}'.format(dataset_url))
    logging.info('SPARQL endpoint is {}'.format(endpoint_url))

    query = f'PREFIX qb: <http://purl.org/linked-data/cube#> PREFIX dim: <http://purl.org/linked-data/sdmx/2009/dimension#> SELECT DISTINCT ?period WHERE {{ ?object a qb:DataSet . ?obs qb:dataSet ?obj ; ?p ?period . ?obs dim:refPeriod ?period . FILTER (?obj = <{dataset_url}>) }}'
    logging.info(f'Query is {query}')

    sparql = SPARQLWrapper(endpoint_url)
    query = sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    result = sparql.query().convert()

    return [x['period']['value'] for x in result['results']['bindings']]

def get_odata_api_periods(distro: Distribution) -> list:
    """
    Given the downloadURL from the scraper, return a list of periods from the odata api
    """
    r = distro._session.get(distro.downloadURL+'$apply=groupby((MonthId))')
    if r.status_code != 200:
        raise Exception(f'failed on url {distro.downloadURL} with code {r.status_code}')
    period_dict = r.json()

    periods = [x["MonthId"] for x in period_dict["value"]]

    formatted_periods = []
    for period in periods:
        
        # format as per pmd
        year = str(period)[:4]
        month = str(period)[-2:]
        period = f'/month/{year}-{month}'
        formatted_periods.append(period)

    return formatted_periods
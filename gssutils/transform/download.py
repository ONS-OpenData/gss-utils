from io import BytesIO
import json

import logging
import pyexcel
import xypath
import messytables
import requests
import backoff
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import ExpiresAfter

from gssutils.metadata.mimetype import ExcelTypes, ODS

class FormatError(Exception):
    """ Raised when the available file format can't be used
    """

    def __init__(self, message):
        self.message = message


def get_simple_databaker_tabs(distro, **kwargs):
    """
    Given a distribution object represening a spreadsheet, attempes to return a list
    of databaker tables objects.
    """
    if distro.mediaType in ExcelTypes:
        with distro.open() as fobj:
            tableset = messytables.excel.XLSTableSet(fileobj=fobj)
            tabs = list(xypath.loader.get_sheets(tableset, "*"))
            return tabs
    elif distro.mediaType == ODS:
        with distro.open() as ods_obj:
            excel_obj = BytesIO()
            book = pyexcel.get_book(file_type='ods', file_content=ods_obj, library='pyexcel-ods3')
            book.save_to_memory(file_type='xls', stream=excel_obj)
            tableset = messytables.excel.XLSTableSet(fileobj=excel_obj)
            tabs = list(xypath.loader.get_sheets(tableset, "*"))
            return tabs
    raise FormatError(f'Unable to load {distro.mediaType} into Databaker.')


def get_simple_csv_pandas(distro, **kwargs):
    """
    Given a distribution object, attempes to return the data as a pandas dataframe
    of dictionary of dataframes (in the case of a spreadsheet source)
    """
    if distro.mediaType in ExcelTypes:
            with distro.open() as fobj:
                # pandas 0.25 now tries to seek(0), so we need to read and buffer the stream
                buffered_fobj = BytesIO(fobj.read())
                return pd.read_excel(buffered_fobj, **kwargs)
    elif distro.mediaType == ODS:
        with distro.open() as ods_obj:
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
    elif distro.mediaType == 'text/csv':
        with distro.open() as csv_obj:
            return pd.read_csv(csv_obj, **kwargs)
    elif distro.mediaType == 'application/json':
        # Assume odata
        to_fetch = distro.downloadURL
        tables = []
        while to_fetch is not None:
            data = distro._session.get(to_fetch).json()
            tables.append(pd.read_json(json.dumps(data['value']), orient='records'))
            if 'odata.nextLink' in data and data['odata.nextLink'] != '':
                to_fetch = data['odata.nextLink']
            else:
                to_fetch = None
        return pd.concat(tables, ignore_index=True)
    raise FormatError(f'Unable to load {distro.mediaType} into Pandas DataFrame.')


def get_principle_dataframe(distro, chunks_wanted: list = None):
    """
    Given a distribution object and a list of chunks of data we want
    return a dataframe
    """
    principle_url = distro.downloadURL
    key = distro._seed['odataConversion']['chunkColumn']

    principle_df = pd.DataFrame()

    if chunks_wanted is not None:
        if type(chunks_wanted) is list:
            for chunk in chunks_wanted:
                url = f"{principle_url}?$filter={key} eq {chunk}"
                principle_df = principle_df.append(_get_odata_data(distro, url))
        else:
            chunk = str(chunks_wanted)
            url = f"{principle_url}?$filter={key} eq {chunk}"
            principle_df = principle_df.append(_get_odata_data(distro, url))
    else: 
        url = principle_url
        principle_df = _get_odata_data(distro, url)

    return principle_df

def get_supplementary_dataframes(distro) -> dict:
    """
    Supplement the base dataframe with expand and foreign deifnition calls etc
    """

    sup = distro._seed['odataConversion']['supplementalEndpoints']
    
    sup_dfs = {}

    # use the longer session cache
    long_cache = get_long_cache_session(distro)

    for name, sup_dict in sup.items():
        sup_dfs[name] = _get_odata_data(distro, sup_dict["endpoint"], session=long_cache)

    return sup_dfs

def get_long_cache_session(distro):
    """
    Get or create a 2nd, longer living cache session
    """
    long_cache = CacheControl(requests.Session(),
                            cache=FileCache('.cache2'),
                            heuristic=ExpiresAfter(days=30))
    return long_cache


@backoff.on_exception(backoff.expo, (requests.exceptions.Timeout, requests.exceptions.ConnectionError))
def _get_odata_data(distro, url, session=None) -> pd.DataFrame():

        # If explicitly passed a session use it, otherwise use the default scraper one
        this_session = session if session is not None else distro._session

        r = this_session.get(url)
        logging.info("Trying url: " + url)
        if r.status_code != 200:
            raise Exception(f'Failed to get data from {url} with status code {r.status_code}')

        contents = r.json()
        df = pd.DataFrame(contents['value'])
        while '@odata.nextLink' in contents.keys():
            page = this_session.get(contents['@odata.nextLink'])
            contents = page.json()
            df = df.append(pd.DataFrame(contents['value']))
        return df

def merge_principle_supplementary_dataframes(distro, principle_df, supplementary_df_dict):
    """
    Given a principle odata datframe and a dictionary of supplementary dataframes, merge the
    supplementary data into the principle dataframe. 
    """

    sup = distro._seed['odataConversion']['supplementalEndpoints']

    for df_name, attributes in sup.items():
        primaryKey = attributes['primaryKey']
        foreignKey = attributes['foreignKey']

        principle_df = pd.merge(principle_df, supplementary_df_dict[df_name], how='left',
                                left_on=foreignKey, right_on=primaryKey)

    return principle_df

def construct_odata_dataframe(distro, chunks_wanted: list = None):
    """
    Construct a dataframe via a series of api calls.
    """

    # Confirm we've been given the required chunks
    if chunks_wanted is None:
        raise Exception('When constructing an odata dataset, you need to pass in a "chunks_wanted" keyword argument')
 
    # use those chunks to construct the principle dataframe
    priciple_df = get_principle_dataframe(distro, chunks_wanted)

    # expand this dataframe with supplementary data
    supplementary_df_dict = get_supplementary_dataframes(distro)

    # merge the principle and supplementary datasets
    df = merge_principle_supplementary_dataframes(distro, priciple_df, supplementary_df_dict)

    return df

def get_pmd_chunks(distro) -> list:
    """
    Given the downloadURL from the scraper, return a list of chunks from pmd4
    """

    # Assumption that no cases of multiple datasets from a single API endpoint, so...
    dataset_url = distro._seed['odataConversion']['datasetIdentifier']
    endpoint_url = distro._seed['odataConversion']['publishedLocation']
    print (distro._seed['odataConversion'])
    chunkDimension = distro._seed['odataConversion']['chunkDimension']
    print(distro._seed['odataConversion'].keys())
    distro._seed['odataConversion']['datasetIdentifier']



    query = f'PREFIX qb: <http://purl.org/linked-data/cube#> PREFIX dim: <http://purl.org/linked-data/sdmx/2009/dimension#> SELECT DISTINCT ?chunk WHERE {{ ?obs qb:dataSet <{dataset_url}>; {chunkDimension} ?chunk . }}'
    logging.info(f'Query is {query}')

    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    result = sparql.query().convert()

    return [x['chunk']['value'] for x in result['results']['bindings']]

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
def get_odata_api_chunks(distro) -> list:
    """
    Given the downloadURL from the scraper, return a list of chunks from the odata api
    """

    r = distro._session.get(distro.downloadURL+'?$apply=groupby((MonthId))')
    if r.status_code != 200:
        raise Exception(f'failed on url {distro.downloadURL} with code {r.status_code}')
    chunk_dict = r.json()

    chunks = [x["MonthId"] for x in chunk_dict["value"]]

    return chunks

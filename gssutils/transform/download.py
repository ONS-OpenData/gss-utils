
from io import BytesIO

import xypath
import messytables
import requests
import backoff
import pandas as pd
import logging
from SPARQLWrapper import SPARQLWrapper, JSON

from gssutils.metadata.mimetype import ExcelTypes, ODS

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


def find_missing_periods(odata_api_periods: list, pmd_periods: list) -> list:
    """
    Given two lists, one of periods from the odata api, another of periods
    from pmd. Return items that are on the api but not pmd.
    """
    
    # TODO - this function! returning everything for now
    return odata_api_periods


def get_principle_dataframe(distro, periods_wanted: list = None):
    """
    Given a distribution object and a list of periods of data we want
    return a dataframe
    """
    principle_url = distro.downloadURL
    key = distro.info['odatConversion']['periodColumn']

    principle_df = pd.dataframe()

    if len(periods_wanted) is not None:
        for period in periods_wanted:
            url = f"{principle_url}$filter={key} eq {period}"
            principle_df = principle_df.append(_get_odata_data(url))
            
    else: 
        url = principle_url
        principle_df = _get_odata_data(url)

    return principle_df

def get_supplimentary_dataframes(distro) -> dict:
    """
    Supplement the base dataframe with expand and foreign deifnition calls etc
    """

    sup = distro.info['odatConversion']['supplementalEndpoints']
    
    sup_dfs = {}

    for name, url in sup, sup['endpoint']:
        sup_dfs[name] = _get_odata_data(url)

    return sup_dfs

def _get_odata_data(url) -> pd.DataFrame():

        #@backoff.on_exception(backoff.expo, (requests.exceptions.Timeout, requests.exceptions.ConnectionError))

        sess = requests.session()
        cached_sess = CacheControl(sess, cache=FileCache('.cache'), heuristic=ExpiresAfter(days=7))

        page = cached_sess.get(url)
        contents = page.json()
        df = pd.DataFrame(contents['value'])
        # print('Fetching data from {url}.'.format(url=page.url))
        while '@odata.nextLink' in contents.keys():
            # print('Fetching more data from {url}.'.format(url=contents['@odata.nextLink']))
            page = cached_sess.get(contents['@odata.nextLink'])
            contents = page.json()
            df = df.append(pd.DataFrame(contents['value']))
        return df

def construct_odata_dataframe(distro, periods_wanted: list = None):
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

def get_pmd_periods(distro) -> list:
    """
    Given the downloadURL from the scraper, return a list of periods from pmd4
    """

    # Assumption that no cases of multiple datasets from a single API endpoint, so...
    dataset_url = distro._seed['odataConversion']['datasetIdentifier']
    endpoint_url = distro._seed['odataConversion']['publishedLocation']
    distro._seed['odataConversion']['datasetIdentifier']

    query = f'PREFIX qb: <http://purl.org/linked-data/cube#> PREFIX dim: <http://purl.org/linked-data/sdmx/2009/dimension#> SELECT DISTINCT ?period WHERE {{ ?obs qb:dataSet <{dataset_url}>; dim:refPeriod ?period . }}'
    logging.info(f'Query is {query}')

    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    result = sparql.query().convert()

    return [x['period']['value'] for x in result['results']['bindings']]

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
def get_odata_api_periods(distro) -> list:
    """
    Given the downloadURL from the scraper, return a list of periods from the odata api
    """

    r = distro._session.get(distro.downloadURL+'$apply=groupby((MonthId))')
    if r.status_code != 200:
        raise Exception(f'failed on url {distro.downloadURL} with code {r.status_code}')
    period_dict = r.json()

    periods = [x["MonthId"] for x in period_dict["value"]]

    return periods

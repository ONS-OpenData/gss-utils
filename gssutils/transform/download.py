import json
import logging
from io import BytesIO

import backoff
import messytables
import pandas as pd
import pyexcel
import requests
import xypath
from typing import Union, Dict, Optional

from gssutils.metadata.base import Resource
from gssutils.metadata.mimetype import ExcelTypes, ODS


class FormatError(Exception):
    """ Raised when the available file format can't be used
    """

    def __init__(self, message):
        self.message = message


class Downloadable(Resource):
    """
    Mixin for downloadable resources, adding as_pandas() and as_databaker() methods.
    Expects self.uri to be a web resource.
    Expects self._mediaType to be set to determine the file type of the downloadable resource.
    Expects self._session to be a re-usable requests session object.
    Expects self._seed to be a dictionary for configuration.
    """

    def __init__(self):
        super().__init__()
        self._session = None
        self._seed = None
        self._mediaType = None

    def open(self):
        stream = self._session.get(self.uri, stream=True).raw
        stream.decode_content = True
        return stream

    def as_databaker(self, **kwargs):
        return self._get_simple_databaker_tabs(**kwargs)

    def as_pandas(self, **kwargs):

        if self._seed is not None:
            if "odataConversion" in self._seed.keys():
                return self._construct_odata_dataframe(**kwargs)

        return self._get_simple_csv_pandas(**kwargs)

    def _get_simple_databaker_tabs(self, **kwargs):
        """
        Given a distribution object representing a spreadsheet, attempts to return a list
        of databaker tables objects.
        """
        if self._mediaType in ExcelTypes:
            with self.open() as fobj:
                tableset = messytables.excel.XLSTableSet(fileobj=fobj)
                tabs = list(xypath.loader.get_sheets(tableset, "*"))
                return tabs
        elif self._mediaType == ODS:
            with self.open() as ods_obj:
                excel_obj = BytesIO()
                book = pyexcel.get_book(file_type='ods', file_content=ods_obj, library='pyexcel-ods3')
                book.save_to_memory(file_type='xls', stream=excel_obj)
                tableset = messytables.excel.XLSTableSet(fileobj=excel_obj)
                tabs = list(xypath.loader.get_sheets(tableset, "*"))
                return tabs
        raise FormatError(f'Unable to load {self._mediaType} into Databaker.')

    def _get_simple_csv_pandas(self, **kwargs) -> Union[Dict[str, pd.DataFrame], pd.DataFrame]:
        """
        Given a distribution object, attempts to return the data as a pandas dataframe
        or dictionary of dataframes (in the case of a spreadsheet source)
        """
        if self._mediaType in ExcelTypes:
            with self.open() as fobj:
                # pandas 0.25 now tries to seek(0), so we need to read and buffer the stream
                buffered_fobj = BytesIO(fobj.read())
                return pd.read_excel(buffered_fobj, **kwargs)
        elif self._mediaType == ODS:
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
        elif self._mediaType == 'text/csv':
            with self.open() as csv_obj:
                return pd.read_csv(csv_obj, **kwargs)
        elif self._mediaType == 'application/json':
            # Assume odata

            return self._get_principle_dataframe()
        raise FormatError(f'Unable to load {self._mediaType} into Pandas DataFrame.')

    def _get_principle_dataframe(self, chunks_wanted: Optional[list] = None):
        """
        Given a distribution object and a list of chunks of data we want
        return a dataframe
        """
        
        principle_df = pd.DataFrame()

        if chunks_wanted is not None:
            key = self._seed['odataConversion']['chunkColumn']

            if type(chunks_wanted) is list:
                for chunk in chunks_wanted:
                    principle_df = principle_df.append(self._get_odata_data(self.uri, params={
                        '$filter': f'{key} eq {chunk}'
                    }))
            else:
                chunk = str(chunks_wanted)
                principle_df = principle_df.append(self._get_odata_data(self.uri, params={
                    '$filter': f'{key} eq {chunk}'
                }))
        else:
            principle_df = self._get_odata_data(self.uri)

        return principle_df

    def _get_supplementary_dataframes(self) -> dict:
        """
        Supplement the base dataframe with expand and foreign principle_df calls etc
        """

        sup = self._seed['odataConversion']['supplementalEndpoints']

        sup_dfs = {}

        for name, sup_dict in sup.items():
            sup_dfs[name] = self._get_odata_data(sup_dict["endpoint"])

        return sup_dfs

    @backoff.on_exception(backoff.expo, (requests.exceptions.Timeout, requests.exceptions.ConnectionError))
    def _get_odata_data(self, url: str, params: Optional[dict] = None) -> pd.DataFrame():
        r = self._session.get(url, params=params)
        logging.info(f"Trying {url} with params {params}")
        if r.status_code != 200:
            raise Exception(f'Failed to get data from {url} with status code {r.status_code}')

        contents = r.json()
        df = pd.DataFrame(contents['value'])

        # This one supports OData (Stat Wales)
        while 'odata.nextLink' in contents.keys():
            page = self._session.get(contents['odata.nextLink'])
            contents = page.json()
            df = df.append(pd.DataFrame(contents['value']))

        # This one supports OData (HMRC Trade UK API)
        while '@odata.nextLink' in contents.keys():
            page = self._session.get(contents['@odata.nextLink'])
            contents = page.json()
            df = df.append(pd.DataFrame(contents['value']))
            
        return df

    def _merge_principle_supplementary_dataframes(self, principle_df, supplementary_df_dict):
        """
        Given a principle oData dataframe and a dictionary of supplementary dataframes, merge the
        supplementary data into the principle dataframe.
        """

        sup = self._seed['odataConversion']['supplementalEndpoints']

        for df_name, attributes in sup.items():
            primary_key = attributes['primaryKey']
            foreign_key = attributes['foreignKey']

            principle_df = pd.merge(principle_df, supplementary_df_dict[df_name], how='left',
                                    left_on=foreign_key, right_on=primary_key)

        return principle_df

    def _construct_odata_dataframe(self, chunks_wanted: Optional[list] = None):
        """
        Construct a dataframe via a series of api calls.
        """

        # Confirm we've been given the required chunks
        if chunks_wanted is None:
            raise Exception(
                'When constructing an odata dataset, you need to pass in a "chunks_wanted" keyword argument')

        # use those chunks to construct the principle dataframe
        principle_df = self._get_principle_dataframe(chunks_wanted)

        # expand this dataframe with supplementary data
        supplementary_df_dict = self._get_supplementary_dataframes()

        # merge the principle and supplementary datasets
        df = self._merge_principle_supplementary_dataframes(principle_df, supplementary_df_dict)

        return df

    def get_pmd_chunks(self) -> list:
        """
        Given the downloadURL from the scraper, return a list of chunks from pmd4
        """

        # Assumption that no cases of multiple datasets from a single API endpoint, so...
        dataset_url = self._seed['odataConversion']['datasetIdentifier']
        endpoint_url = self._seed['odataConversion']['publishedLocation']
        logging.debug(self._seed['odataConversion'])
        chunk_dimension = self._seed['odataConversion']['chunkDimension']
        logging.debug(self._seed['odataConversion'].keys())

        query = f'''PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX dim: <http://purl.org/linked-data/sdmx/2009/dimension#>
SELECT DISTINCT ?chunk WHERE {{
    ?obs qb:dataSet <{dataset_url}>; <{chunk_dimension}> ?chunk .
}}'''
        logging.info(f'Query is {query}')

        result = self._session.post(endpoint_url,
                                    headers={'Accept': 'application/sparql-results+json'},
                                    data={'query': query}).json()

        return [x['chunk']['value'] for x in result['results']['bindings']]

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
    def get_odata_api_chunks(self) -> list:
        """
        Given the downloadURL from the scraper, return a list of chunks from the odata api
        """

        r = self._session.get(self.uri, params={'$apply': 'groupby((MonthId))'})
        if r.status_code != 200:
            raise Exception(f'failed on url {self.uri} with code {r.status_code}')
        chunk_dict = r.json()

        chunks = [x["MonthId"] for x in chunk_dict["value"]]

        return chunks

import csv
import json
import logging
from collections import namedtuple
from pathlib import Path
from typing import NamedTuple, List, Optional, Union, Mapping

from gssutils import pathify

default_map = {
    "Value": {
        "unit": "#unit/count",
        "measure": "#measure/total",
        "datatype": "integer"
    }
}


class Datatype(NamedTuple):
    base: Optional[str] = None
    format: Optional[str] = None


class Column(NamedTuple):
    name: str
    titles: Union[str, List[str], None] = None
    datatype: Union[str, Datatype, None] = None
    suppressOutput: Optional[bool] = None
    virtual: Optional[bool] = None
    required: Optional[bool] = None
    propertyUrl: Optional[str] = None
    valueUrl: Optional[str] = None


class ColumnReference(NamedTuple):
    resource: str
    columnReference: str


class ForeignKey(NamedTuple):
    columnReference: str
    reference: ColumnReference


class TableSchema(NamedTuple):
    columns: List[Column]
    primaryKey: Optional[list] = None
    foreignKeys: Optional[List[ForeignKey]] = None


class Table(NamedTuple):
    url: str
    tableSchema: Union[str, TableSchema]
    suppressOutput: Optional[bool] = None


class CSVWMapping:
    def __init__(self):
        self._csv_filename: str = None
        self._csv_stream = None
        self._mapping = {}
        self._columns: Mapping[str, Column] = {}
        self._external_tables = []

    @staticmethod
    def namify(column_header: str):
        return pathify(column_header).replace('-', '_')

    def set_csv(self, csv_filename):
        with open(csv_filename, newline='', encoding='utf-8') as f:
            self.set_input(csv_filename, f)

    def set_input(self, filename, stream):
        self._csv_stream = stream
        self._csv_filename = filename
        reader = csv.DictReader(stream)
        for col in reader.fieldnames:
            self._columns[col] = Column(name=CSVWMapping.namify(col), titles=col, datatype="string")

    def set_mapping(self, mapping):
        if 'transform' in mapping and 'columns' in mapping['transform']:
            self._mapping = mapping['transform']['columns']
        else:
            logging.error(f'No column mapping found.')

    def _as_csvw_object(self):
        if self._mapping is not None:
            for name, obj in self._mapping.items():
                if name in self._columns:
                    if "property" in obj and "value" in obj:
                        self._columns[name] = self._columns[name]._replace(
                            propertyUrl=obj["property"],
                            valueUrl=obj["value"]
                        )
                    if "unit" in obj and "measure" in obj:
                        self._columns[name] = self._columns[name]._replace(propertyUrl=obj["measure"])
                        if "datatype" in obj:
                            self._columns[name] = self._columns[name]._replace(datatype=obj["datatype"])
                        else:
                            self._columns[name] = self._columns[name]._replace(datatype="number")
                        self._columns["virt_unit"] = Column(
                            name="virt_unit",
                            virtual=True,
                            propertyUrl="http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure",
                            valueUrl=obj["unit"]
                        )
                        self._columns["virt_measure"] = Column(
                            name="virt_measure",
                            virtual=True,
                            propertyUrl="http://purl.org/linked-data/cube#measureType",
                            valueUrl=obj["measure"]
                        )
        return {
            "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
            "tables": self._as_tables()
        }

    def _as_tables(self):
        return self._external_tables + [{
            "url": self._csv_filename,
            "tableSchema": {
                "columns": list(self._columns.values()),
                "primaryKey": []
            }
        }]

    @staticmethod
    def _as_plain_obj(o):
        if isinstance(o, tuple):
            try:
                return {k: CSVWMapping._as_plain_obj(v) for (k, v) in dict(o._asdict()).items() if v is not None}
            except AttributeError:
                return o
        elif isinstance(o, dict):
            return {k: CSVWMapping._as_plain_obj(v) for (k, v) in o.items()}
        elif isinstance(o, Path):
            return str(o)
        elif isinstance(o, list):
            return [CSVWMapping._as_plain_obj(i) for i in o]
        else:
            return o

    def write(self, stream):
        plain_obj = CSVWMapping._as_plain_obj(self._as_csvw_object())
        logging.warn(json.dumps(plain_obj, indent=2))
        json.dump(plain_obj, stream)

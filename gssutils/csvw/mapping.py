import csv
import json
import logging
from pathlib import Path
from typing import NamedTuple, List, Optional, Union, Mapping, Dict, TextIO, Any, Set
from urllib.parse import urljoin

from uritemplate import variables

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


class Resource(NamedTuple):
    at_id: str
    at_type: Union[str, List[str]]


class Component(NamedTuple):
    at_type: Union[str, List[str]] = "qb:ComponentSpecification"
    qb_componentProperty: Optional[Resource] = None


class DSD(NamedTuple):
    at_id: str = '#structure'
    at_type: Union[str, List[str]] = "qb:DataStructureDefinition"
    qb_component: List[Component] = []


class DataSet(NamedTuple):
    at_id: str = '#dataset'
    at_type: Union[str, List[str]] = ["qb:DataSet", "dcat:Dataset"]
    qb_structure: DSD = DSD()


class CSVWMapping:
    def __init__(self):
        self._csv_filename: Optional[str] = None
        self._csv_stream: Optional[TextIO] = None
        self._mapping: Dict[str, Any] = {}
        self._columns: Dict[str, Column] = {}
        self._external_tables: List[Table] = []
        self._dataset_uri: str = ''
        self._dataset = DataSet()

    @staticmethod
    def namify(column_header: str):
        return pathify(column_header).replace('-', '_')

    def set_csv(self, csv_filename: str):
        with open(csv_filename, newline='', encoding='utf-8') as f:
            self.set_input(csv_filename, f)

    def set_input(self, filename: str, stream: TextIO):
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

    def set_dataset_uri(self, uri):
        self._dataset_uri = uri

    def _validate(self):
        # check variable names are consistent
        declared_names = set([col.name for col in self._columns.values()])
        used_names: Set[str] = set()
        for name_set in (
            variables(t)
            for col in self._columns.values()
            for t in [col.propertyUrl, col.valueUrl]
            if t is not None
        ):
            used_names.update(name_set)
        if not declared_names.issuperset(used_names):
            logging.error(f"Unmatched variable names: {used_names.difference(declared_names)}")

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
        self._validate()
        return {
            "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
            "tables": self._as_tables(),
            "@id": urljoin(self._dataset_uri, "#tables", allow_fragments=True),
            "prov:hadDerivation": self._dataset
        }

    def _as_tables(self):
        return self._external_tables + [Table(
            url=self._csv_filename,
            tableSchema=TableSchema(
                columns=list(self._columns.values()),
                primaryKey=[]
            )
        )]

    @staticmethod
    def _as_plain_obj(o):
        def fix_prefix(key: str):
            for prefix, replace in {'at_': '@', 'qb_': 'qb:'}.items():
                if key.startswith(prefix):
                    return replace + key[len(prefix):]
            return key
        if isinstance(o, tuple):
            try:
                return {fix_prefix(k): CSVWMapping._as_plain_obj(v) for (k, v) in dict(o._asdict()).items() if v is not None}
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

    def write(self, stream: TextIO):
        plain_obj = CSVWMapping._as_plain_obj(self._as_csvw_object())
        logging.debug(json.dumps(plain_obj, indent=2))
        json.dump(plain_obj, stream)

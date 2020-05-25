import csv
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, TextIO, Any, Set, Union
from urllib.parse import urljoin

from uritemplate import variables

from gssutils import pathify
from gssutils.csvw.dsd import DataSet, DimensionComponent, MeasureComponent, AttributeComponent, Component, \
    DimensionProperty, DSD, Resource, MeasureProperty
from gssutils.csvw.namespaces import prefix_map, URI
from gssutils.csvw.table import Column, TableSchema, Table

default_map = {
    "Value": {
        "unit": "#unit/count",
        "measure": "#measure/total",
        "datatype": "integer"
    }
}


class CSVWMapping:
    def __init__(self):
        self._csv_filename: Optional[str: URI] = None
        self._csv_stream: Optional[TextIO] = None
        self._mapping: Dict[str, Any] = {}
        self._columns: Dict[str, Column] = {}
        self._external_tables: List[Table] = []
        self._dataset_uri: URI = URI('')
        self._dataset = DataSet()
        self._components: List[Component] = []
        self._registry: Optional[URI] = None

    @staticmethod
    def namify(column_header: str):
        return pathify(column_header).replace('-', '_')

    def set_csv(self, csv_filename: URI):
        with open(csv_filename, newline='', encoding='utf-8') as f:
            self.set_input(csv_filename, f)

    def set_input(self, filename: URI, stream: TextIO):
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

    def set_registry(self, uri: URI):
        self._registry = uri

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
        # check used prefixes
        used_prefixes = set(
            t.split(':')[0]
            for col in self._columns.values()
            for t in [col.propertyUrl, col.valueUrl]
            if t is not None and not t.startswith('http') and ':' in t
        )
        if not set(prefix_map.keys()).issuperset(used_prefixes):
            logging.error(f"Unknown prefixes used: {used_prefixes.difference(prefix_map.keys())}")

    def _as_csvw_object(self):
        if self._mapping is not None:
            for name, obj in self._mapping.items():
                if name in self._columns:
                    if "property" in obj and "value" in obj:
                        self._columns[name] = self._columns[name]._replace(
                            propertyUrl=URI(obj["property"]),
                            valueUrl=URI(obj["value"])
                        )
                        self._components.append(DimensionComponent(
                            at_id=URI(f"#component/{self._columns[name].name}"),
                            qb_componentProperty=Resource(at_id=URI(obj["property"])),
                            qb_dimension=DimensionProperty(
                                at_id=URI(obj["property"]),
                                rdfs_range=Resource(
                                    at_id=URI(f"#class/{self._columns[name].name}")
                                )
                            )
                        ))
                    if "unit" in obj and "measure" in obj:
                        self._columns[name] = self._columns[name]._replace(propertyUrl=obj["measure"])
                        if "datatype" in obj:
                            self._columns[name] = self._columns[name]._replace(datatype=obj["datatype"])
                        else:
                            self._columns[name] = self._columns[name]._replace(datatype="number")
                        self._components.extend([
                            DimensionComponent(
                                at_id=URI("#component/measure_type"),
                                qb_componentProperty=Resource(at_id=URI("http://purl.org/linked-data/cube#measureType")),
                                qb_dimension=DimensionProperty(
                                    at_id=URI("http://purl.org/linked-data/cube#measureType"),
                                    rdfs_range=Resource(at_id=URI("http://purl.org/linked-data/cube#MeasureProperty"))
                                )
                            ),
                            MeasureComponent(
                                at_id=URI(f"#component/{self._columns[name].name}"),
                                qb_componentProperty=Resource(at_id=obj["measure"]),
                                qb_measure=MeasureProperty(at_id=obj["measure"])
                            )
                        ])
                        self._columns["virt_unit"] = Column(
                            name="virt_unit",
                            virtual=True,
                            propertyUrl=URI("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"),
                            valueUrl=URI(obj["unit"])
                        )
                        self._columns["virt_measure"] = Column(
                            name="virt_measure",
                            virtual=True,
                            propertyUrl=URI("http://purl.org/linked-data/cube#measureType"),
                            valueUrl=URI(obj["measure"])
                        )
        self._validate()
        return {
            "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
            "tables": self._as_tables(),
            "@id": urljoin(self._dataset_uri, "#tables", allow_fragments=True),
            "prov:hadDerivation": DataSet(
                qb_structure=DSD(
                    qb_component=self._components
                )
            )
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
            for prefix, replace in {'at_': '@', 'qb_': 'qb:', 'rdfs_': 'rdfs:'}.items():
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

import csv
import gzip
import json
import logging
from io import TextIOBase
from pathlib import Path
from typing import List, Optional, Dict, TextIO, Any, Set, Union
from urllib.parse import urljoin
import re

from uritemplate import variables, URITemplate

from gssutils import pathify
from gssutils.csvw.dsd import DataSet, DimensionComponent, MeasureComponent, AttributeComponent, Component, \
    DimensionProperty, DSD, Resource, MeasureProperty, AttributeProperty
from gssutils.csvw.namespaces import prefix_map, URI
from gssutils.csvw.table import Column, TableSchema, Table, ForeignKey

default_map = {
    "Value": {
        "unit": "#unit/count",
        "measure": "#measure/total",
        "datatype": "integer"
    }
}


class CSVWMapping:
    def __init__(self):
        self._csv_filename: Optional[URI] = None
        self._csv_stream: Optional[TextIO] = None
        self._mapping: Dict[str, Any] = {}
        self._column_names: List[str] = []
        self._columns: Dict[str, Column] = {}
        self._external_tables: List[Table] = []
        self._dataset_uri: Optional[URI] = None
        self._dataset_root_uri: Optional[URI] = None
        self._dataset = DataSet()
        self._components: List[Component] = []
        self._registry: Optional[URI] = None
        self._keys: List[str] = []
        self._metadata_filename: Optional[URI] = None
        self._foreign_keys: Optional[List[ForeignKey]] = None
        self._measureTemplate: Optional[URITemplate] = None
        self._measureTypes: Optional[List[str]] = None

    @staticmethod
    def namify(column_header: str):
        return pathify(column_header).replace('-', '_')

    @staticmethod
    def classify(column_header: str):
        return ''.join(part.capitalize() for part in pathify(column_header).split('-'))

    def join_dataset_uri(self, relative: str, use_true_dataset_root: bool = False):
        # treat the dataset URI as an entity that when joined with a fragment, just adds
        # the fragment, but when joined with a relative path, turns the dataset URI into a container
        # by adding a / to the end before adding the relative path

        f"""
        Where datasets have multiple distinct dataframes, `self._dataset_uri` is of the form
            http://gss-data.org.uk/data/gss_data/<family_path>/<dataset_root_path>/<dataset_path>

        Codelists are defined at the `dataset_root_path` level, so we need to be able to create URIs relative to
            http://gss-data.org.uk/data/gss_data/<family_path>/<dataset_root_path>
        """
        root_uri = self._dataset_root_uri if use_true_dataset_root else self._dataset_uri

        if root_uri is None:
            return URI(relative)
        elif relative.startswith('#'):
            return URI(urljoin(root_uri, relative, allow_fragments=True))
        else:
            return URI(urljoin(root_uri + '/', relative, allow_fragments=True))

    def set_csv(self, csv_filename: URI):

        # csv and csv.gz need to be read in slightly different ways
        if str(csv_filename).endswith("csv"):
            with open(csv_filename, newline='', encoding='utf-8') as f:
                self.set_input(csv_filename, f)
        elif str(csv_filename).endswith("csv.gz"):
            with gzip.open(csv_filename, encoding='utf-8') as f:
                self.set_input(csv_filename, f)
        else:
            raise ValueError("Only csv types of .csv and /csv.gz are supported."
                    " Not {}".format(csv_filename))

    def set_input(self, filename: URI, stream: TextIO):
        self._csv_stream = stream
        self._csv_filename = Path(str(filename)[:-3]) if str(filename).endswith(".csv.gz") else filename
        reader = csv.DictReader(stream)
        self._column_names = reader.fieldnames
        for col in self._column_names:
            self._columns[col] = Column(name=CSVWMapping.namify(col), titles=col, datatype="string")

    def set_mapping(self, mapping):
        if 'transform' in mapping and 'columns' in mapping['transform']:
            self._mapping = mapping['transform']['columns']
        else:
            logging.error(f'No column mapping found.')

    def set_additional_foreign_key(self, foreign_key: ForeignKey):
        if self._foreign_keys is None:
            self._foreign_keys = []
        self._foreign_keys.append(foreign_key)

    def set_dataset_uri(self, uri: URI, dataset_root_uri: Optional[URI] = None):
        f"""
        Please make sure you set the dataset_root_uri.

        If this dataset has only one dataframe associated then both {uri} and {dataset_root_uri} should be the same, 
        e.g.
            `http://gss-data.org.uk/data/gss_data/<family-name>/<dataset-name>`

        If the dataset has more than one dataframe associated and so has a {uri} of the form
            `http://gss-data.org.uk/data/gss_data/<family-name>/<dataset-name>/<dataframe-name>`
        then the {dataset_root_uri} must represent the URI fragment common to all dataframes, e.g.
            `http://gss-data.org.uk/data/gss_data/<family-name>/<dataset-name>`
        """
        self._dataset_uri = uri

        if dataset_root_uri is None:
            print("WARNING: dataset_root_uri is unset. " +
                  "In future this warning will be converted to an error and terminate your build.")

            # Legacy compatibility code:
            # This code will NOT survive any change is URI standards.
            if self._dataset_uri is not None:
                matches: re.Match = re.match("^(.+)/gss_data/([^/]+)/([^/]+).*$", self._dataset_uri,
                                             re.RegexFlag.IGNORECASE)
                base_uri = f"{matches.group(1)}/gss_data"
                family_path = matches.group(2)
                dataset_root_path = matches.group(3)
                dataset_root_uri = f"{base_uri}/{family_path}/{dataset_root_path}"

        self._dataset_root_uri = dataset_root_uri

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
        def get_conventional_local_codelist_scheme_uri(column_name: str) -> Resource:
            codelist_uri = self.join_dataset_uri(f"#scheme/{pathify(column_name)}", use_true_dataset_root=True)
            return Resource(at_id=codelist_uri)

        def get_maybe_codelist_for_col(column_config: object, column_name: str) -> Optional[Resource]:
            if "codelist" in column_config:
                codelist = column_config["codelist"]
                if isinstance(codelist, bool) and not codelist:
                    # Config explicitly forbids a codelist being linked here.
                    return None

                return Resource(at_id=codelist)

            # Codelist should exist. Convention dictates it should be a local codelist.
            return get_conventional_local_codelist_scheme_uri(column_name)

        def get_convential_local_codelist_concept_uri_template(column_name: str) -> URI:
            return self.join_dataset_uri(f"#concept/{pathify(column_name)}/{{{self._columns[column_name].name}}}",
                                         use_true_dataset_root=True)

        def get_value_uri_template_for_col(column_def: object, column_name: str) -> URI:
            if "value" in column_def:
                return URI(column_def["value"])

            return get_convential_local_codelist_concept_uri_template(column_name)

        # Look to see whether the measure type has its own column
        for map_name, map_obj in self._mapping.items():
            if "dimension" in map_obj and map_obj["dimension"] == "http://purl.org/linked-data/cube#measureType":
                self._measureTemplate = URITemplate(map_obj["value"])
                if "types" in map_obj:
                    self._measureTypes = map_obj["types"]
                    # add a component specification for each measure
                    for t in map_obj["types"]:
                        template_vars = {CSVWMapping.namify(map_name): t}
                        self._components.append(
                            MeasureComponent(
                                at_id=self.join_dataset_uri(f"#component/{pathify(t)}"),
                                qb_componentProperty=Resource(at_id=self._measureTemplate.expand(template_vars)),
                                qb_measure=MeasureProperty(at_id=self._measureTemplate.expand(template_vars))
                            )
                        )
        # Now iterate over column headers in the given CSV file
        for name in self._column_names:
            if self._mapping is not None and name in self._mapping and isinstance(self._mapping[name], dict):
                obj = self._mapping[name]
                if "dimension" in obj and "value" in obj:
                    self._keys.append(self._columns[name].name)
                    self._columns[name] = self._columns[name]._replace(
                        propertyUrl=URI(obj["dimension"]),
                        valueUrl=URI(obj["value"])
                    )
                    self._components.append(DimensionComponent(
                        at_id=self.join_dataset_uri(f"#component/{pathify(name)}"),
                        qb_componentProperty=Resource(at_id=URI(obj["dimension"])),
                        qb_dimension=DimensionProperty(
                            at_id=URI(obj["dimension"]),
                            rdfs_range=Resource(
                                at_id=self.join_dataset_uri(f"#class/{CSVWMapping.classify(name)}")
                            )
                        )
                    ))
                elif "parent" in obj and "value" in obj:
                    # a local dimension that has a super property
                    description: Optional[str] = obj.get("description", None)
                    label: str = obj.get("label", name)
                    source: Optional[Resource] = None
                    if "source" in obj:
                        source = Resource(at_id=URI(obj["source"]))
                    self._keys.append(self._columns[name].name)
                    self._columns[name] = self._columns[name]._replace(
                        propertyUrl=self.join_dataset_uri(f"#dimension/{pathify(name)}"),
                        valueUrl=get_value_uri_template_for_col(obj, name)
                    )
                    self._components.append(DimensionComponent(
                        at_id=self.join_dataset_uri(f"#component/{pathify(name)}"),
                        qb_componentProperty=Resource(at_id=self.join_dataset_uri(f"#dimension/{pathify(name)}")),
                        qb_dimension=DimensionProperty(
                            at_id=self.join_dataset_uri(f"#dimension/{pathify(name)}"),
                            rdfs_range=Resource(
                                at_id=self.join_dataset_uri(f"#class/{CSVWMapping.classify(name)}")
                            ),
                            qb_codeList=get_maybe_codelist_for_col(obj, name),
                            rdfs_label=label,
                            rdfs_comment=description,
                            rdfs_subPropertyOf=Resource(at_id=URI(obj["parent"])),
                            rdfs_isDefinedBy=source
                        )
                    ))
                elif "description" in obj or "label" in obj:
                    # local dimension with a definition/label and maybe source of the definition
                    description: Optional[str] = obj.get("description", None)
                    label: Optional[str] = obj.get("label", name)
                    source: Optional[Resource] = None
                    if "source" in obj:
                        source = Resource(at_id=URI(obj["source"]))
                    self._keys.append(self._columns[name].name)
                    self._columns[name] = self._columns[name]._replace(
                        propertyUrl=self.join_dataset_uri(f"#dimension/{pathify(name)}"),
                        valueUrl=get_value_uri_template_for_col(obj, name)
                    )
                    self._components.append(DimensionComponent(
                        at_id=self.join_dataset_uri(f"#component/{pathify(name)}"),
                        qb_componentProperty=Resource(at_id=self.join_dataset_uri(f"#dimension/{pathify(name)}")),
                        qb_dimension=DimensionProperty(
                            at_id=self.join_dataset_uri(f"#dimension/{pathify(name)}"),
                            rdfs_range=Resource(
                                at_id=self.join_dataset_uri(f"#class/{CSVWMapping.classify(name)}")
                            ),
                            qb_codeList=get_maybe_codelist_for_col(obj, name),
                            rdfs_label=label,
                            rdfs_comment=description,
                            rdfs_isDefinedBy=source
                        )
                    ))
                elif "attribute" in obj and "value" in obj:
                    self._columns[name] = self._columns[name]._replace(
                        propertyUrl=URI(obj["attribute"]),
                        valueUrl=URI(obj["value"])
                    )
                    self._components.append(AttributeComponent(
                        at_id=self.join_dataset_uri(f"#component/{pathify(name)}"),
                        qb_componentProperty=Resource(at_id=URI(obj["attribute"])),
                        qb_attribute=AttributeProperty(
                            at_id=URI(obj["attribute"]),
                            rdfs_range=Resource(
                                at_id=self.join_dataset_uri(f"#class/{CSVWMapping.classify(name)}")
                            )
                        )
                    ))
                elif "unit" in obj and "measure" in obj:
                    self._columns[name] = self._columns[name]._replace(propertyUrl=obj["measure"])
                    if "datatype" in obj:
                        self._columns[name] = self._columns[name]._replace(datatype=obj["datatype"])
                    else:
                        self._columns[name] = self._columns[name]._replace(datatype="number")
                    self._components.extend([
                        DimensionComponent(
                            at_id=self.join_dataset_uri("#component/measure_type"),
                            qb_componentProperty=Resource(at_id=URI("http://purl.org/linked-data/cube#measureType")),
                            qb_dimension=DimensionProperty(
                                at_id=URI("http://purl.org/linked-data/cube#measureType"),
                                rdfs_range=Resource(at_id=URI("http://purl.org/linked-data/cube#MeasureProperty"))
                            )
                        ),
                        MeasureComponent(
                            at_id=self.join_dataset_uri(f"#component/{pathify(name)}"),
                            qb_componentProperty=Resource(at_id=obj["measure"]),
                            qb_measure=MeasureProperty(at_id=obj["measure"])
                        ),
                        AttributeComponent(
                            at_id=self.join_dataset_uri(f"#component/unit"),
                            qb_componentProperty=Resource(
                                at_id=URI("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure")
                            ),
                            qb_attribute=AttributeProperty(
                                at_id=URI("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure")
                            )
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
                elif "datatype" in obj and not ("measure" in obj or "unit" in obj):
                    # Where a measure type column exists
                    assert self._measureTemplate is not None, "Must have a measure type column."
                    self._columns[name] = self._columns[name]._replace(
                        propertyUrl=self._measureTemplate.uri,
                        datatype=obj["datatype"]
                    )
            elif self._mapping is not None and name in self._mapping and isinstance(self._mapping[name], bool):
                self._columns[name] = self._columns[name]._replace(
                    suppressOutput=not self._mapping[name]
                )
            else:
                # assume local dimension, with optional definition
                description: Optional[str] = None
                if self._mapping is not None and name in self._mapping and isinstance(self._mapping[name], str):
                    description = self._mapping[name]
                self._keys.append(self._columns[name].name)
                self._columns[name] = self._columns[name]._replace(
                    propertyUrl=self.join_dataset_uri(f"#dimension/{pathify(name)}"),
                    valueUrl=get_convential_local_codelist_concept_uri_template(name)
                )
                self._components.append(DimensionComponent(
                    at_id=self.join_dataset_uri(f"#component/{pathify(name)}"),
                    qb_componentProperty=Resource(at_id=self.join_dataset_uri(f"#dimension/{pathify(name)}")),
                    qb_dimension=DimensionProperty(
                        at_id=self.join_dataset_uri(f"#dimension/{pathify(name)}"),
                        rdfs_range=Resource(
                            at_id=self.join_dataset_uri(f"#class/{CSVWMapping.classify(name)}")
                        ),
                        qb_codeList=get_conventional_local_codelist_scheme_uri(name),
                        rdfs_label=name,
                        rdfs_comment=description
                    )
                ))
        self._columns["virt_dataset"] = Column(
            name="virt_dataset",
            virtual=True,
            propertyUrl=URI("qb:dataSet"),
            valueUrl=URI(self.join_dataset_uri("#dataset"))
        )
        self._columns["virt_type"] = Column(
            name="virt_type",
            virtual=True,
            propertyUrl=URI("rdf:type"),
            valueUrl=URI("qb:Observation")
        )
        self._validate()
        return {
            "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
            "tables": self._as_tables(),
            "@id": self.join_dataset_uri("#tables"),
            "prov:hadDerivation": DataSet(
                at_id=self.join_dataset_uri('#dataset'),
                qb_structure=DSD(
                    at_id=self.join_dataset_uri('#structure'),
                    qb_component=self._components
                )
            )
        }

    def _as_tables(self):
        table_uri = URI(Path(self._csv_filename).name)  # default is that metadata is filename + '-metadata.json'
        if self._metadata_filename is not None:
            table_uri = URI(self._csv_filename.relative_to(self._metadata_filename.parent))
        main_table = Table(
            url=table_uri,
            tableSchema=TableSchema(
                columns=list(self._columns.values()),
                primaryKey=self._keys,
                aboutUrl=self.join_dataset_uri('/'.join('{' + s + '}' for s in self._keys)),
                foreignKeys=self._foreign_keys
            )
        )
        return self._external_tables + [main_table]

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

    def write(self, out: Union[URI, TextIO]):
        if not isinstance(out, TextIOBase):
            self._metadata_filename = out
            stream = open(out, "w", encoding="utf-8")
        else:
            stream = out
        plain_obj = CSVWMapping._as_plain_obj(self._as_csvw_object())
        logging.debug(json.dumps(plain_obj, indent=2))
        json.dump(plain_obj, stream, indent=2)

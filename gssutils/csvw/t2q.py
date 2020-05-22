import argparse
import csv
import json
import logging
from codecs import iterdecode
from typing import Dict, Any
from pathlib import Path
from urllib import request, parse
from urllib.parse import urljoin

from rdflib import URIRef, RDF, Literal

from gssutils.csvw.namespaces import prefix_map
from gssutils.utils import pathify


class CSVWMetadata:

    def __init__(self, ref_base):
        # Reference data has moved, but rather than change every notebook,
        # we redirect and log a deprecation.
        if ref_base.startswith('https://ons-opendata'):
            self._ref_base = f"https://gss-cogs{ref_base[len('https://ons-opendata'):]}"
            logging.warning(f"{ref_base} has been re-written to {self._ref_base}, please update usage.")
        else:
            self._ref_base = ref_base
        self._col_def = CSVWMetadata._csv_lookup(
            parse.urljoin(self._ref_base, 'columns.csv'), 'title')
        self._comp_def = CSVWMetadata._csv_lookup(

            parse.urljoin(self._ref_base, 'components.csv'), 'Label')
        self._codelists: Dict[str, Any] = {}
        for table in json.load(request.urlopen(parse.urljoin(self._ref_base, 'codelists-metadata.json')))['tables']:
            codelist_url = f'http://gss-data.org.uk/def/concept-scheme/{pathify(table["rdfs:label"])}'
            self._codelists[codelist_url] = table
        # need to resolve ref_common against relative URIs

    @staticmethod
    def _csv_lookup(url: str, key: str) -> Dict[str, Dict[str, str]]:
        stream = request.urlopen(url)
        reader = csv.DictReader(iterdecode(stream, 'utf-8'))
        return {row[key]: row for row in reader}

    def create(self, csv_filename, schema_filename, with_transform=False,
               base_url=None, base_path=None, dataset_metadata=None, with_external=True):
        with open(csv_filename) as csv_io:
            with open(schema_filename, 'w') as schema_io:
                if with_transform:
                    self.create_io(csv_io, schema_io, str(csv_filename.relative_to(schema_filename.parent)),
                                   with_transform, base_url, base_path, dataset_metadata, with_external)
                else:
                    self.create_io(csv_io, schema_io, str(csv_filename.relative_to(schema_filename.parent)))

    def create_io(self, csv_io, schema_io, csv_url, with_transform=False, mapping=None,
                  base_url=None, base_path=None, dataset_metadata=None, with_external=True):
        schema_columns = []
        schema_tables = []
        schema_references = []
        schema_keys = []
        dsd_components = []
        reader = csv.DictReader(csv_io)
        measure_types = set()
        if with_transform: # need to figure out the measure types used
            measure_types.update(row['Measure Type'] for row in reader)
        column_map = {}
        if mapping is not None:
            column_map = json.load(mapping)
        for column in reader.fieldnames:
            if column in column_map:
                pass
            elif column in self._col_def:
                column_def = self._col_def[column]
                is_unit = column_def['property_template'] == 'http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure'
                column_schema = {
                    'titles': column,
                    'required': is_unit or (column_def['component_attachment'] not in ['qb:attribute', '']),
                    'name': column_def['name']
                }
                if 'regex' in column_def and column_def['regex'] not in (None, ''):
                    if column_def['datatype'] != 'string':
                        print(f"Column definition has regular expression guard '{column_def['regex']}' but datatype is '{column_def['datatype']}'")
                    else:
                        column_schema['datatype'] = {
                            'format': column_def['regex']
                        }
                else:
                    column_schema['datatype'] = column_def['datatype']
                if with_transform:
                    column_schema['propertyUrl'] = column_def['property_template']
                    if 'value_template' in column_def and column_def['value_template'] != '' and column_def['value_template'] is not None:
                        column_schema['valueUrl'] = column_def['value_template']
                schema_columns.append(column_schema)
                if column in self._comp_def:
                    component_def = self._comp_def[column]
                    codelist = component_def['Codelist']
                    if codelist in self._codelists:
                        reference = parse.urljoin(self._ref_base,
                                                  self._codelists[component_def['Codelist']]['url'])
                        table_schema_url = urljoin(self._ref_base,
                                                   self._codelists[component_def['Codelist']]['tableSchema'])
                        if with_external:
                            schema_tables.append({
                                'url': reference,
                                'tableSchema': table_schema_url,
                                'suppressOutput': True
                            })
                            schema_references.append({
                                'columnReference': column_def['name'],
                                'reference': {
                                    'resource': reference,
                                    'columnReference': 'notation'
                                }
                            })
                    elif codelist.startswith('http://gss-data.org.uk/def/concept-scheme'):
                        print(f"Potentially missing concept scheme <{codelist}>")
                if (is_unit and not with_transform) or (column_def['component_attachment'] not in ['', 'qb:attribute']):
                    schema_keys.append(column_def['name'])
                if with_transform and column_def['component_attachment'] != '':
                    comp_attach = {
                        '@id': column_def['property_template'],
                        '@type': {
                            'qb:dimension': 'qb:DimensionProperty',
                            'qb:attribute': 'qb:AttributeProperty'
                        }.get(column_def['component_attachment'])
                    }
                    if 'range' in column_def and column_def['range'] not in ['', None]:
                        comp_attach['rdfs:range'] = {'@id': column_def['range']}
                    if column in self._comp_def:
                        codelist = self._comp_def[column]['Codelist']
                        if codelist is not None and codelist != '':
                            comp_attach['qb:codelist'] = {'@id': codelist}
                            if 'rdfs:range' not in comp_attach:
                                comp_attach['rdfs:range'] = {'@id': 'http://www.w3.org/2004/02/skos/core#ConceptScheme'}
                    dsd_def = {
                        '@id': urljoin(base_url, base_path) + '/component/' + column_def['name'],
                        '@type': 'qb:ComponentSpecification',
                        'qb:componentProperty': {'@id': column_def['property_template']},
                        column_def['component_attachment']: comp_attach
                    }
                    dsd_components.append(dsd_def)
            else:
                print(f'"{column}" not defined')

        if with_transform:
            for measure_type in measure_types:
                measure_def = next(d for d in self._col_def.values() if pathify(d['title']) == measure_type)
                comp_attach = {
                    '@id': measure_def['property_template'],
                    '@type': 'qb:MeasureProperty'
                }
                if 'range' in measure_def and measure_def['range'] not in ['', None]:
                    comp_attach['rdfs:range'] = {'@id': measure_def['range']}
                dsd_def = {
                    '@id': urljoin(base_url, base_path) + '/component/' + measure_def['name'],
                    '@type': 'qb:ComponentSpecification',
                    'qb:componentProperty': {'@id': measure_def['property_template']},
                    measure_def['component_attachment']: comp_attach
                }
                dsd_components.append(dsd_def)
            schema_columns.append({
                'name': 'dataset_ref',
                'virtual': True,
                'propertyUrl': 'qb:dataSet',
                'valueUrl': urljoin(base_url, base_path)
            })
            schema_columns.append({
                'name': 'qbtype',
                'virtual': True,
                'propertyUrl': 'rdf:type',
                'valueUrl': 'qb:Observation'
            })

        table_schema =  {
            "columns": schema_columns,
            "primaryKey": schema_keys
        }
        if with_external:
            table_schema["foreignKeys"] = schema_references
        schema_tables.append({
            "url": csv_url,
            "tableSchema": table_schema
        })
        if with_transform:
            about_path = base_path + '/' + '/'.join(f'{{{key}}}' for key in schema_keys)
            about_url = urljoin(base_url, str(about_path))
            schema_tables[-1]['tableSchema']['aboutUrl'] = about_url

        schema = {
            "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
            "tables": schema_tables
        }
        if with_transform:
            dataset_uri = urljoin(base_url, base_path)
            schema['@id'] = dataset_uri + '#tablegroup'
            ds_meta = {
                '@id': dataset_uri,
                '@type': ['qb:DataSet'],
                'qb:structure': {
                    '@id': urljoin(dataset_uri + '/', 'structure'),
                    '@type': 'qb:DataStructureDefinition',
                    'qb:component': dsd_components
                }
            }
            if dataset_metadata is not None:
                def csvw_prefix(uri):
                    for prefix, namespace in prefix_map.items():
                        if uri.startswith(namespace):
                            return f'{prefix}:{uri[len(namespace):]}'
                    return None
                for s, p, o, g in dataset_metadata.quads((URIRef(dataset_uri), None, None, None)):
                    if p == RDF.type:
                        t = csvw_prefix(str(o))
                        if t is not None:
                            ds_meta['@type'].append(t)
                    else:
                        prefixed_p = csvw_prefix(str(p))
                        if prefixed_p is not None:
                            if type(o) == Literal:
                                if o.datatype is not None:
                                    ds_meta[prefixed_p] = {
                                        '@value': str(o),
                                        '@type': o.datatype
                                    }
                                else:
                                    ds_meta[prefixed_p] = str(o)
                            elif type(o) == URIRef:
                                ds_meta[prefixed_p] = { '@id': str(o) }
            schema['prov:hadDerivation'] = ds_meta

        json.dump(schema, schema_io, indent=2)


def create_schema():
    parser = argparse.ArgumentParser(description='Create CSV schema')
    parser.add_argument(
        'config_base_url',
        help='Base URL for table2qb configuration files, columns.csv, components,csv and codelists-metadata.json'
    )
    parser.add_argument('csv_file', type=argparse.FileType('r'),
                        help='Input CSV file with headers matching definitions in columns.csv.')
    parser.add_argument('schema_file', type=argparse.FileType('w'),
                        help='Output JSON file for use by CSVW validation tool, e.g. csvlint.')
    args = parser.parse_args()
    csvw = CSVWMetadata(args.config_base_url)
    csvw.create_io(
        args.csv_file,
        args.schema_file,
        str(Path(args.csv_file.name).relative_to(Path(args.schema_file.name).parent)))


def create_transform():
    parser = argparse.ArgumentParser(description='Create CSVW JSON for transformation')
    parser.add_argument(
        'config_base_url',
        help='Base URL for table2qb style configuration files, columns.csv, components.csv and codelsits-metadata.json'
    )
    parser.add_argument(
        'about_base_url',
        help='Base URL for the eventual observations.'
    )
    parser.add_argument(
        'about_path',
        help='Path to append to URL for observations.'
    )
    parser.add_argument('csv_file', type=argparse.FileType('r'),
                        help='Input CSV file with headers matching definitions in columns.csv.')
    parser.add_argument('json_file', type=argparse.FileType('w'),
                        help='Output CSVW JSON file for use by csv2rdf transformation.')
    args = parser.parse_args()
    csvw = CSVWMetadata(args.config_base_url)
    csvw.create_io(
        args.csv_file,
        args.json_file,
        str(Path(args.csv_file.name).relative_to(Path(args.json_file.name).parent)),
        True, args.about_base_url, args.about_path)
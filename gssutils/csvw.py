import argparse
import csv
import json
from codecs import iterdecode
from pathlib import Path, PosixPath
from urllib import request, parse
from urllib.parse import urljoin

from rdflib import URIRef, RDF, Literal

from gssutils.utils import pathify


csvw_namespaces = {
    "as": "https://www.w3.org/ns/activitystreams#",
    "cc": "http://creativecommons.org/ns#",
    "csvw": "http://www.w3.org/ns/csvw#",
    "ctag": "http://commontag.org/ns#",
    "dc": "http://purl.org/dc/terms/",
    "dc11": "http://purl.org/dc/elements/1.1/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcterms": "http://purl.org/dc/terms/",
    "dctypes": "http://purl.org/dc/dcmitype/",
    "dqv": "http://www.w3.org/ns/dqv#",
    "duv": "https://www.w3.org/TR/vocab-duv#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "gr": "http://purl.org/goodrelations/v1#",
    "grddl": "http://www.w3.org/2003/g/data-view#",
    "ical": "http://www.w3.org/2002/12/cal/icaltzd#",
    "ldp": "http://www.w3.org/ns/ldp#",
    "ma": "http://www.w3.org/ns/ma-ont#",
    "oa": "http://www.w3.org/ns/oa#",
    "og": "http://ogp.me/ns#",
    "org": "http://www.w3.org/ns/org#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "prov": "http://www.w3.org/ns/prov#",
    "qb": "http://purl.org/linked-data/cube#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfa": "http://www.w3.org/ns/rdfa#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rev": "http://purl.org/stuff/rev#",
    "rif": "http://www.w3.org/2007/rif#",
    "rr": "http://www.w3.org/ns/r2rml#",
    "schema": "http://schema.org/",
    "sd": "http://www.w3.org/ns/sparql-service-description#",
    "sioc": "http://rdfs.org/sioc/ns#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "skosxl": "http://www.w3.org/2008/05/skos-xl#",
    "v": "http://rdf.data-vocabulary.org/#",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "void": "http://rdfs.org/ns/void#",
    "wdr": "http://www.w3.org/2007/05/powder#",
    "wrds": "http://www.w3.org/2007/05/powder-s#",
    "xhv": "http://www.w3.org/1999/xhtml/vocab#",
    "xml": "rdf:XMLLiteral",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
}


class CSVWMetadata:

    def __init__(self, ref_base):
        self._ref_base = ref_base
        self._col_def = CSVWMetadata._csv_lookup(
            parse.urljoin(ref_base, 'columns.csv'), 'title')
        self._comp_def = CSVWMetadata._csv_lookup(
            parse.urljoin(ref_base, 'components.csv'), 'Label')
        self._codelists = {}
        for table in json.load(request.urlopen(parse.urljoin(ref_base, 'codelists-metadata.json')))['tables']:
            codelist_url = f'http://gss-data.org.uk/def/concept-scheme/{pathify(table["rdfs:label"])}'
            self._codelists[codelist_url] = table
        # need to resolve ref_common against relative URIs

    @staticmethod
    def _csv_lookup(url, key):
        stream = request.urlopen(url)
        reader = csv.DictReader(iterdecode(stream, 'utf-8'))
        return {row[key]: row for row in reader}

    def create(self, csv_filename, schema_filename, with_transform=False,
               base_url=None, base_path=None, dataset_metadata=None):
        with open(csv_filename) as csv_io:
            with open(schema_filename, 'w') as schema_io:
                if with_transform:
                    self.create_io(csv_io, schema_io, str(csv_filename.relative_to(schema_filename.parent)),
                                   with_transform, base_url, base_path, dataset_metadata)
                else:
                    self.create_io(csv_io, schema_io, str(csv_filename.relative_to(schema_filename.parent)))

    def create_io(self, csv_io, schema_io, csv_url, with_transform=False,
                  base_url=None, base_path=None, dataset_metadata=None):
        schema_columns = []
        schema_tables = []
        schema_references = []
        schema_keys = []
        dsd_components = []
        reader = csv.DictReader(csv_io)
        measure_types = set()
        if with_transform: # need to figure out the measure types used
            measure_types.update(row['Measure Type'] for row in reader)
        for column in reader.fieldnames:
            if column in self._col_def:
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
                        }.get(column_def['component_attachment']),
                        'rdfs:label': column_def['title']
                    }
                    if 'range' in column_def and column_def['range'] not in ['', None]:
                        comp_attach['rdfs:range'] = {'@id': column_def['range']}
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
                measure_def = next(d for d in self._col_def.values() if d['name'] == measure_type)
                comp_attach = {
                    '@id': measure_def['property_template'],
                    '@type': 'qb:MeasureProperty',
                    'rdfs:label': measure_def['title']
                }
                if 'range' in measure_def and measure_def['range'] not in ['', None]:
                    comp_attach['rdfs:range'] = {'@id': measure_def['range']}
                dsd_def = {
                    '@id': urljoin(base_url, base_path) + '/component/' + measure_type,
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

        schema_tables.append({
            "url": csv_url,
            "tableSchema": {
                "columns": schema_columns,
                "foreignKeys": schema_references,
                "primaryKey": schema_keys
            }
        })
        if with_transform:
            about_path = PosixPath(base_path)
            for key in schema_keys:
                about_path = about_path / f'{{{key}}}'
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
                    for prefix, namespace in csvw_namespaces.items():
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
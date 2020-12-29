import re
import csv
from os import path
from typing import List, Dict
import json

from .config import pmdcat_base_uri
from .updates.nodes.utils import override


def create_metadata_shell_for_csv(csv_file_path: str) -> str:
    """
    Returns the path for the metadata file which has been created.
    """
    metadata_file = f"{csv_file_path}-metadata.json"
    if path.exists(metadata_file):
        raise Exception(f"Metadata file {metadata_file} already exists.")
    if not path.exists(csv_file_path):
        raise Exception(f"CSV file {csv_file_path} does not exist.")

    label = _map_file_path_to_label(csv_file_path)
    concept_scheme_uri = _generate_concept_scheme_root_uri(label)

    # Just inserting basic structure at this point as already exists in standard files. Additional metadata will be
    # added as the script continues to run.
    metadata = {
        "@context": "http://www.w3.org/ns/csvw",
        "@id": concept_scheme_uri,
        "url": csv_file_path,
        "rdfs:label": label,
        "dc:title": label,
        "tableSchema": {
            "columns": [],
        },
        "prov:hadDerivation": {
            "@id": concept_scheme_uri,
            "@type": [
                "skos:ConceptScheme",
                f"{pmdcat_base_uri}DatasetContents"
            ]
        }
    }

    table_schema: Dict = metadata["tableSchema"]
    columns: List[Dict] = table_schema["columns"]

    with open(csv_file_path, newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=",", quotechar="\"")
        column_names: List[str] = next(reader)

    for column_name in column_names:
        column = _generate_schema_for_column(column_name, concept_scheme_uri)
        columns.append(column)

    columns.append({
            "virtual": True,
            "propertyUrl": "rdf:type",
            "valueUrl": "skos:Concept"
    })
    columns.append({
            "virtual": True,
            "propertyUrl": "skos:inScheme",
            "valueUrl": concept_scheme_uri
    })

    if "notation" in [c.lower() for c in column_names]:
        override(table_schema, {
            "primaryKey": "notation",
            "aboutUrl": concept_scheme_uri + "/{notation}"
        })
    else:
        print("WARNING: could not determine primary key. As a result, `aboutUrl` property is not specified and " +
              "so each row will not have a true URI. This is basically required. Manual configuration required.")

    with open(metadata_file, 'w+') as file:
        file.write(json.dumps(metadata, indent=4))

    return str(metadata_file)


def _map_file_path_to_label(file_path: str) -> str:
    file_name_without_ext = re.sub(".*?([^/]+)\\..*$", "\\1", file_path)
    return file_name_without_ext.replace("-", " ").title()


def _generate_schema_for_column(column_name: str, concept_scheme_uri: str) -> Dict:
    """
    Generates column schema structure for a given column name.
    If the column name matches one of the standard GSS code-list column names then we link up the associated metadata.
    """
    column_name = column_name.strip()
    column_name_lower = column_name.lower()
    column_name_snake_case = re.sub("\\s+", "_", column_name_lower)
    column = {
        "titles": column_name,
        "name": column_name_snake_case
    }
    if column_name_lower == "label":
        override(column, {
            "datatype": "string",
            "required": True,
            "propertyUrl": "rdfs:label"
        })
    elif column_name_lower == "notation":
        override(column, {
            "datatype": {
                "base": "string",
                "format": "^-?[\\w\\.\\/\\+]+(-[\\w\\.\\/\\+]+)*$"
            },
            "required": True,
            "propertyUrl": "skos:notation"
        })
    elif column_name_lower == "parent notation":
        override(column, {
            "datatype": {
                "base": "string",
                "format": "^(-?[\\w\\.\\/\\+]+(-[\\w\\.\\/\\+]+)*|)$"
            },
            "required": False,
            "propertyUrl": "skos:broader",
            "valueUrl": concept_scheme_uri + "/{" + column_name_snake_case + "}"
        })
    elif column_name_lower == "sort priority":
        override(column, {
            "datatype": "integer",
            "required": False,
            "propertyUrl": "http://www.w3.org/ns/ui#sortPriority"
        })
    elif column_name_lower == "description":
        override(column, {
            "datatype": "string",
            "required": False,
            "propertyUrl": "rdfs:comment"
        })
    else:
        print(f"WARNING: Column '{column_name}' is not standard and so has not been fully mapped. " +
              "Please configure manually.")

    return column


def _generate_concept_scheme_root_uri(label: str):
    def code_list_is_in_family() -> bool:
        global_family_response = input("Is the code list defined at the Global level or at the Family level? (G/f): ") \
            .strip().lower()
        is_global = len(global_family_response) == 0 or global_family_response == "g"
        if not is_global and global_family_response != "f":
            raise Exception(f"Invalid Global or family response '{global_family_response}'")

        return not is_global

    label_uri_format = re.sub("\\s+", "-", label.lower())

    if code_list_is_in_family():
        family_name = input("Please enter the family name (e.g. trade): ").strip().lower()
        if len(family_name) == 0:
            raise Exception("Family Name not provided.")

        return f"{config.reference_data_base_uri}/{family_name}/concept-scheme/{label_uri_format}"
    else:
        return f"{config.reference_data_base_uri}/concept-scheme/{label_uri_format}"
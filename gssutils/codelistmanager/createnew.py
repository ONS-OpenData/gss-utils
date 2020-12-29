import re
import csv
from os import path
from typing import List, Dict
import json
from enum import Enum

from .config import pmdcat_base_uri, reference_data_base_uri
from .updates.nodes.utils import override


class CodeListLevel(Enum):
    Global = 0
    Family = 1
    Dataset = 2


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
    concept_scheme_uri = _generate_concept_scheme_root_uri(csv_file_path, label)

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

    concept_base_uri = _map_concept_scheme_uri_to_concept_base(concept_scheme_uri)
    for column_name in column_names:
        column = _generate_schema_for_column(column_name, concept_base_uri)
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
            "aboutUrl": concept_base_uri + "/{notation}"
        })
    else:
        print("WARNING: could not determine primary key. As a result, `aboutUrl` property is not specified and " +
              "so each row will not have a true URI. This is basically required. Manual configuration required.")

    with open(metadata_file, 'w+') as file:
        file.write(json.dumps(metadata, indent=4))

    return str(metadata_file)


def _map_concept_scheme_uri_to_concept_base(concept_scheme_uri: str) -> str:
    """
    If the URL is one of the dataset-specific `#scheme/code-list-name` variety, then the URI for individual concepts
    is of the form `#concept/code-list-name`. Since this behaviour is driven by gss-utils automatic URI generation,
    it's imperitive that we follow it here.

    Family and Global codelists don't follow this rule and since URIs aren't auto-generated it isn't such a problem.
    """
    hash_url_match_regex = r"(.*)#scheme(/.*)?"
    if re.match(hash_url_match_regex, concept_scheme_uri):
        return re.sub(hash_url_match_regex, "\\1#concept\\2", concept_scheme_uri)
    else:
        return concept_scheme_uri


def _map_file_path_to_label(file_path: str) -> str:
    file_name_without_ext = re.sub(".*?([^/]+)\\..*$", "\\1", file_path)
    return file_name_without_ext.replace("-", " ").title()


def _generate_schema_for_column(column_name: str, concept_base_uri: str) -> Dict:
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
            "valueUrl": concept_base_uri + "/{" + column_name_snake_case + "}"
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


def _generate_concept_scheme_root_uri(csv_file_path: str, label: str):
    label_uri_format = _to_uri_format(label)
    code_list_level = _get_code_list_level()

    if code_list_level == CodeListLevel.Family:
        family_path = _get_family_name_path()
        return f"{reference_data_base_uri}def/{family_path}/concept-scheme/{label_uri_format}"
    elif code_list_level == CodeListLevel.Dataset:
        family_path = _get_family_name_path()
        dataset_path = _get_dataset_name_path(csv_file_path)
        return f"{reference_data_base_uri}data/gss_data/{family_path}/{dataset_path}#scheme/{label_uri_format}"
    else:
        return f"{reference_data_base_uri}def/concept-scheme/{label_uri_format}"


def _get_code_list_level() -> CodeListLevel:
    level_response = input(
        "Is the code list defined at the Global level, the Family level or the Dataset level? (G/f/d): ")\
        .strip().lower()

    if len(level_response) == 0 or level_response == "g":
        return CodeListLevel.Global
    elif level_response == "f":
        return CodeListLevel.Family
    elif level_response == "d":
        return CodeListLevel.Dataset
    else:
        raise Exception(f"Invalid code list level response '{level_response}'")


def _get_dataset_name_path(csv_file_path: str) -> str:
    [dir_path, _] = path.split(path.abspath(csv_file_path))
    [parent_dir_path, _] = path.split(dir_path)
    [_, parent_dir_name] = path.split(parent_dir_path)
    data_set_uri_name: str = parent_dir_name.lower()
    return _to_uri_format(data_set_uri_name)


def _get_family_name_path() -> str:
    family_name = input("Please enter the family name (e.g. trade): ").strip().lower()
    if len(family_name) == 0:
        raise Exception("Family Name not provided.")
    return _to_uri_format(family_name)


def _to_uri_format(input: str) -> str:
    return re.sub("\\s+", "-", input.strip().lower())


from typing import Dict, List
from datetime import datetime

from .updates.dcat import ensure_dcat_metadata_populated
from .updates.standardiselabels import standardise_labels
from .config import pmdcat_base_uri


def refactor_structure_with_updates(csvw_mapping: Dict, allow_human_input: bool):
    if "tables" in csvw_mapping:
        tables: List[Dict] = csvw_mapping["tables"]
        for table in tables:
            if _table_mapping_has_type(table, "skos:ConceptScheme"):
                _refactor_table_mapping_with_updates(table, allow_human_input)
            else:
                id = table["@id"]
                print(f"Ignoring table with ID {id} as it is not a skos:ConceptScheme")

    elif _table_mapping_has_type(csvw_mapping, "skos:ConceptScheme"):
        _refactor_table_mapping_with_updates(csvw_mapping, allow_human_input)
    else:
        id = csvw_mapping["@id"]
        print(f"Ignoring table with ID {id} as it is not a skos:ConceptScheme")


def _table_mapping_has_type(table_mapping: Dict, expected_type: str) -> bool:
    if "prov:hadDerivation" in table_mapping:
        derivation = table_mapping["prov:hadDerivation"]
        if "@type" in derivation:
            t = derivation["@type"]
            return (isinstance(t, list) and expected_type in t) or (
                    isinstance(t, str) and t == expected_type)

    return False


def _refactor_table_mapping_with_updates(table_mapping: Dict, allow_human_input: bool):
    """
    Applies schematic updates to the structure of `.csv-metadata.json` files.
    """

    # Populate our variables.
    dt_now = datetime.now().isoformat()
    concept_scheme_uri: str = table_mapping["@id"]
    csv_url: str = table_mapping["url"]

    print(f"Processing code list {csv_url}")

    standardise_labels(table_mapping)

    catalog_label: str = table_mapping.get("rdfs:label")

    ensure_dcat_metadata_populated(pmdcat_base_uri, allow_human_input, concept_scheme_uri,
                                   table_mapping, dt_now, catalog_label)

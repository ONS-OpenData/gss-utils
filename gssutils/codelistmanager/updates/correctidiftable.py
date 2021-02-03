"""
An upgrade to correct the "@id" property where it is set to "#table".

This only works if we have a column definition which specifies where the skos:ConceptScheme is.
"""
from typing import Dict, List, Optional

from .nodes.utils import find


def _get_concept_scheme_uri_from_cols(cols: List[Dict]) -> Optional[str]:
    for col in cols:
        # "propertyUrl": "skos:inScheme",
        # "valueUrl": "http://gss-data.org.uk/def/concept-scheme/labour-market-age-categories"
        property_url = col.get("propertyUrl")
        value_url = col.get("valueUrl")
        if property_url is not None and property_url == "skos:inScheme" and value_url is not None:
            return value_url

    return None


def correct_id_if_table(
        table_mapping: Dict
):
    table_id = table_mapping["@id"]
    if table_id != "#table":
        return

    # Else, the table has it #table. This is wrong.
    if "tableSchema" in table_mapping:
        table_schema = table_mapping["tableSchema"]
        if "columns" in table_schema:
            columns = table_schema["columns"]
            concept_scheme_uri = _get_concept_scheme_uri_from_cols(columns)
            if concept_scheme_uri is not None:
                table_mapping["@id"] = concept_scheme_uri

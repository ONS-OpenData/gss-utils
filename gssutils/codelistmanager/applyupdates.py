from typing import Dict
from datetime import datetime

from .updates.dcat import ensure_dcat_metadata_populated
from .updates.standardiselabels import standardise_labels
from .config import pmdcat_base_uri


def refactor_structure_with_updates(csvw_mapping: Dict, allow_human_input: bool):
    """
    Applies schematic updates to the structure of `.csv-metadata.json` files.
    """

    # Populate our variables.
    dt_now = datetime.now().isoformat()
    concept_scheme_uri: str = csvw_mapping["@id"]
    csv_url: str = csvw_mapping["url"]

    print(f"Processing code list {csv_url}")

    standardise_labels(csvw_mapping)

    catalog_label: str = csvw_mapping.get("rdfs:label")

    ensure_dcat_metadata_populated(pmdcat_base_uri, allow_human_input, concept_scheme_uri,
                                   csvw_mapping, dt_now, catalog_label)

from typing import Dict


def standardise_labels(
        csvw_mapping: Dict
):
    """
    Historical place for rdfs:label doesn't make much sense as it's inside `prov:hadDerivation`.
    This update moves it outside of this object and ensures both `rdfs:label` and `dc:title` are set.
    """
    prov_derivation_object = csvw_mapping["prov:hadDerivation"]
    existing_label: str = csvw_mapping.get("rdfs:label", prov_derivation_object.get("rdfs:label"))

    if "rdfs:label" in prov_derivation_object:
        prov_derivation_object.pop("rdfs:label")
    # Ensure all labels are set in correct location.
    csvw_mapping["rdfs:label"] = existing_label
    csvw_mapping["dc:title"] = existing_label

from .nodes.dataset import configure_dataset_node, is_dataset_node
from .nodes.catalogrecord import configure_catalog_record, is_catalog_record_node
from .nodes.catalogrecordlink import configure_catalog_record_link, is_catalog_record_link_node
from .nodes.utils import find

from typing import Dict, Union, List


def ensure_dcat_metadata_populated(
        pmdcat_base_uri: str,
        allow_human_input: bool,
        concept_scheme_uri: str,
        table_mapping: Dict,
        dt_now: str,
        catalog_label: str
):
    """
    Ensures that the relevant PMDCAT and DCAT metadata is linked to the ConceptScheme.
    """
    prov_derivation_object = table_mapping["prov:hadDerivation"]

    catalog_record_uri = concept_scheme_uri + "/catalog-record"
    dataset_uri = concept_scheme_uri + "/dataset"

    _ensure_type_updated(pmdcat_base_uri, prov_derivation_object)

    # Ensure rdfs:seeAlso section is populated with dcat:CatalogRecord,
    # dcat:Dataset and a link between the top-level codelist catalog and the CatalogRecord for this codelist.
    rdfs_see_also: List[Dict] = table_mapping.get("rdfs:seeAlso", [])
    dataset_node = find(rdfs_see_also, is_dataset_node)
    if not dataset_node:
        dataset_node = {}
        rdfs_see_also.append(dataset_node)
    configure_dataset_node(
        pmdcat_base_uri,
        dataset_node,
        allow_human_input,
        concept_scheme_uri,
        dataset_uri,
        catalog_label
    )

    catalog_record_catalog_link = find(rdfs_see_also, is_catalog_record_link_node)
    if not catalog_record_catalog_link:
        catalog_record_catalog_link = {}
        rdfs_see_also.append(catalog_record_catalog_link)
    configure_catalog_record_link(catalog_record_catalog_link, catalog_record_uri)

    catalog_record = find(rdfs_see_also, is_catalog_record_node)
    if not catalog_record:
        catalog_record = {}
        rdfs_see_also.append(catalog_record)
    configure_catalog_record(pmdcat_base_uri, catalog_record, catalog_record_uri, concept_scheme_uri, dataset_uri,
                             dt_now, catalog_label)

    table_mapping["rdfs:seeAlso"] = rdfs_see_also


def _ensure_type_updated(pmdcat_base_uri: str, prov_derivation_object: Dict):
    """
    Ensure that the skos:ConceptScheme is also of type pmdcat:DatasetContents
    """
    existing_type: Union[str, List[str]] = prov_derivation_object["@type"]
    pmdcat_dataset_contents = f"{pmdcat_base_uri}DatasetContents"
    pmdcat_concept_scheme = f"{pmdcat_base_uri}ConceptScheme"
    if isinstance(existing_type, str):
        if existing_type != pmdcat_concept_scheme:
            prov_derivation_object["@type"] = [
                existing_type,
                pmdcat_concept_scheme
            ]
    elif isinstance(existing_type, list):
        if pmdcat_concept_scheme not in existing_type:
            existing_type.append(pmdcat_concept_scheme)

        if pmdcat_dataset_contents in existing_type:
            existing_type.remove(pmdcat_dataset_contents)
    else:
        raise Exception(
            f"Unexpected datatype found for '@types': {type(existing_type)}")

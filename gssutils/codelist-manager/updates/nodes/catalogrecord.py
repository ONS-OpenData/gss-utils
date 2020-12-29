from utils import override, supplement, node_has_type
from typing import Dict


def is_catalog_record_node(node: Dict) -> bool:
    node_has_type(node, "dcat:CatalogRecord")


def configure_catalog_record(
        pmdcat_base_uri: str,
        catalog_record: Dict,
        catalog_record_uri: str,
        concept_root_uri: str,
        dataset_uri: str,
        dt_now: str,
        catalog_label: str
):
    override(catalog_record, {
        "@id": catalog_record_uri,
        "@type": "dcat:CatalogRecord",
        "foaf:primaryTopic": {
            "@id": dataset_uri
        },
        f"{pmdcat_base_uri}metadataGraph": {
            "@id": concept_root_uri
        }
    })
    supplement(catalog_record, {
        "dc:title": f"{catalog_label} Catalog Record",
        "rdfs:label": f"{catalog_label} Catalog Record",
        "dc:issued": {
            "@type": "dateTime",
            "@value": dt_now
        },
        "dc:modified": {
            "@type": "dateTime",
            "@value": dt_now
        }
    })

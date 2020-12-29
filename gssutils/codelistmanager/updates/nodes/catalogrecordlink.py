from typing import Dict

from .utils import override


def is_catalog_record_link_node(node: Dict) -> bool:
    return "dcat:record" in node


def configure_catalog_record_link(catalog_record_catalog_link: Dict, catalog_record_uri: str):
    override(catalog_record_catalog_link, {
        "@id": "http://gss-data.org.uk/catalog/vocabularies",
        "dcat:record": {"@id": catalog_record_uri}
    })

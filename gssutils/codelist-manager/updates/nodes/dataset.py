from typing import Dict
from utils import node_has_type, override, supplement
import datetime


def is_dataset_node(node: Dict) -> bool:
    return node_has_type(node, "dcat:Dataset")


def configure_dataset_node(
        pmdcat_base_uri: str,
        dataset_node: Dict,
        allow_human_input: bool,
        concept_scheme_uri: str,
        dataset_uri: str,
        catalog_label: str
):
    override(dataset_node, {
        "@id": dataset_uri,
        "@type": [
            "dcat:Dataset",
            f"{pmdcat_base_uri}Dataset"
        ],
        f"{pmdcat_base_uri}datasetContents": {
            "@id": concept_scheme_uri
        },
        f"{pmdcat_base_uri}graph": {
            "@id": concept_scheme_uri
        }
    })

    supplement(dataset_node, {
        "rdfs:label": catalog_label,
        "dc:title": catalog_label,
        "rdfs:comment": f"Dataset representing the '{catalog_label}' code list."
    })

    if allow_human_input:
        # Get the user to provide some inputs:
        fields = [
            {
                "name": "dc:license",
                "input_request": "Please provide the license URI",
                "to_value": lambda input_value: {"@id": input_value}
            },
            {
                "name": "dc:creator",
                "input_request": "Creator Identifier URI",
                "to_value": lambda input_value: {"@id": input_value}
            },
            {
                "name": "dc:publisher",
                "input_request": "Publisher Identifier URI",
                "to_value": lambda input_value: {"@id": input_value}
            },
            {
                "name": "dcat:contactPoint",
                "input_request": "Contact Point URI (accepts 'mailto:email@address.com')",
                "to_value": lambda input_value: {"@id": input_value}
            },
            {
                "name": "dcat:landingPage",
                "input_request": "Landing Page URL (user landing for Download)",
                "to_value": lambda landing_uri: {"@id": landing_uri}
            },
            {
                "name": "dc:issued",
                "input_request": "Date issued/created/published (YYYY-mm-dd)",
                "to_value": lambda input_value: {"@type": "dateTime",
                                                 "@value": datetime.strptime(input_value, "%Y-%m-%d").isoformat()}
            },
            {
                "name": "dc:modified",
                "input_request": "Date modified (YYYY-mm-dd)",
                "to_value": lambda input_value: {"@type": "dateTime",
                                                 "@value": datetime.strptime(input_value, "%Y-%m-%d").isoformat()}
            },
            {
                "name": f"{pmdcat_base_uri}markdownDescription",
                "input_request": "Markdown Description of Dataset",
                "to_value": lambda input_value: {
                    "@type": "https://www.w3.org/ns/iana/media-types/text/markdown#Resource",
                    "@value": input_value
                }
            }
        ]

        for field in fields:
            field_name = field["name"]
            to_value = field["to_value"]
            input_request = field["input_request"]
            if field_name not in dataset_node:
                input_value = input(f"{input_request}: ").strip()
                if len(input_value) > 0:
                    dataset_node[field_name] = to_value(input_value)

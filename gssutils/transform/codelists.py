
import json

from pathlib import Path
from gssutils import pathify

# TODO - this is awful but we're out of time,
# Replace and use classes from .metadata to construct in a more OOP way


def get_codelist_schema(column_label, base_url, dataset_title):
        """
        Given a column label representing a codelist, generate a codelist schema
        """

        # TODO - use a class not random hacky json

        # TODO - seriously fugly
        plain_text_name = "{" + "name" + "}" 
        codelistname = "{" + pathify(column_label) + "}"
        label = "{label" + "}"
        notation = "{notation" + "}"
        pathifed_title = pathify(dataset_title)

        columns = [
            {
              "titles": "label",
              "name": "label",
              "datatype": "string",
              "required": True,
              "propertyUrl": "rdfs:label",
              "valueUrl": f"{label}"
            },
            {
              "titles": "notation",
              "name": "notation",
              "datatype": {
                "base": "string",
                "format": "^-?[\\w\\.\\/]+(-[\\w\\.\\/]+)*$"
              },
              "required": True,
              "propertyUrl": "skos:notation",
              "valueUrl": f"{notation}"
            },
            {
              "titles": "parent_notation",
              "name": "parent_notation",
              "datatype": {
                "base": "string",
                "format": "^(-?[\\w\\.\\/]+(-[\\w\\.\\/]+)*|)$"
              },
              "required": False,
              "propertyUrl": "skos:broader",
              "valueUrl": "{parent-notation}"
            },
            {
              "titles": "sort_priority",
              "name": "sort_priority",
              "datatype": "number",
              "required": False,
              "propertyUrl": "http://www.w3.org/ns/ui#sortPriority",
              "valueUrl": "{sort-priority}"
            },
            {
              "name": "top_concept_of",
              "datatype": "string",
              "propertyUrl": "skos:topConceptOf",
              "valueUrl": f"{base_url}/def/concept-scheme/{codelistname}",
              "virtual": True
            },
            {
              "name": "pref_label",
              "datatype": "string",
              "propertyUrl": "skos:prefLabel",
              "valueUrl": f"{label}",
              "virtual": True
            },
            {
              "name": "in_scheme",
              "propertyUrl": "skos:inScheme",
              "valueUrl": f"{base_url}/def/concept-scheme/{codelistname}",
              "virtual": True
            },
            {
              "name": "type",
              "propertyUrl": "rdf:type",
              "valueUrl": "skos:Concept",
              "virtual": True
            },
            {
              "name": "has_top_concept",
              "propertyUrl": "skos:hasTopConcept",
              "valueUrl": f"{base_url}/def/concept/{codelistname}/{notation}",
              "virtual": True
            },
            {
              "name": "member",
              "propertyUrl": "skos:member",
              "valueUrl": f"{base_url}/def/concept/{codelistname}/{notation}",
              "virtual": True
            }
        ]

        # TODO - ugly
        table_schema = {
            "@id": f"{base_url}/def/concept-scheme/{pathifed_title}/{codelistname}",
            "aboutUrl": f"{base_url}/def/concept-scheme/{codelistname}",
            "url": f"codelist-{pathify(column_label)}-schema.csv",
            "columns": columns,
            "primaryKey": ["notation", "parent_notation"],
            "prov:hadDerivation": {
                "@id": f"{base_url}/def/concept-scheme/{codelistname}",
                "@type": "skos:ConceptScheme",
                "rdfs:label": f"Code list for {column_label} codelist schema",
                "skos:prefLabel": f"Code list for {column_label} codelist schema"
                }
        }

        schema = {
            "@context": [
                "http://www.w3.org/ns/csvw",
                {
                "@language": "en"
                }],
            "@id": f"http://gss-data.org.uk/def/{codelistname}#tablegroup",
            "tables": [table_schema]
        }

        return schema


def generate_codelist_schema(column_label, destination, base_url, dataset_title):
        schema = get_codelist_schema(column_label, base_url, dataset_title)
        schema_path = Path(destination / "codelist-{}.schema.json".format(pathify(column_label)))
        with open(schema_path, "w") as f:
            f.write(json.dumps(schema, indent=2))
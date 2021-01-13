Feature: Create and Manage CodeList Metadata files
  I want to be able to create metadata files for CSV files.
  I want to be able to upgrade existing metadata files to conform to incrementally improved standards.

  Scenario: Move Label from Old Position to New Position
    Given We have a metadata file of the form
      """
      {
        "@context": "http://www.w3.org/ns/csvw",
        "@id": "http://some.id",
        "url": "some-file.csv",
        "tableSchema": {
          "columns": []
        },
        "prov:hadDerivation": {
          "@id": "http://some.id",
          "@type": "skos:ConceptScheme",
          "rdfs:label": "Some Code List"
        }
      }
      """
    When We run an automatic upgrade on the metadata file
    Then The following properties are set
      """
      {
        "rdfs:label": "Some Code List",
        "dc:title": "Some Code List"
      }
      """
    And The following properties are not set
      """
      {
        "prov:hasDerivation": {
          "rdfs:label": true
        }
      }
      """

  Scenario: Add PMDCAT/DCAT Metadata to Existing Metadata Files
    Given We have a metadata file of the form
      """
      {
        "@context": "http://www.w3.org/ns/csvw",
        "@id": "http://some.id",
        "url": "some-file.csv",
        "tableSchema": {
          "columns": []
        },
        "prov:hadDerivation": {
          "@id": "http://some.id",
          "@type": "skos:ConceptScheme"
        },
        "rdfs:label": "Some Code List",
        "dct:label": "Some Code List"
      }
      """
    When We run an automatic upgrade on the metadata file
    Then The following properties are set
      """
      {
        "prov:hadDerivation": {
          "@type": [
            "skos:ConceptScheme",
            "http://publishmydata.com/pmdcat#ConceptScheme"
          ]
        },
        "rdfs:seeAlso": [
          {
              "@id": "http://some.id/dataset",
              "@type": [
                  "dcat:Dataset",
                  "http://publishmydata.com/pmdcat#Dataset"
              ],
              "http://publishmydata.com/pmdcat#datasetContents": {
                  "@id": "http://some.id"
              },
              "rdfs:label": "Some Code List",
              "dc:title": "Some Code List",
              "rdfs:comment": "Dataset representing the 'Some Code List' code list.",
              "http://publishmydata.com/pmdcat#graph": {
                  "@id": "http://some.id"
              }
          },
          {
              "@id": "http://gss-data.org.uk/catalog/vocabularies",
              "dcat:record": {
                  "@id": "http://some.id/catalog-record"
              }
          },
          {
              "@id": "http://some.id/catalog-record",
              "@type": "dcat:CatalogRecord",
              "foaf:primaryTopic": {
                  "@id": "http://some.id/dataset"
              },
              "dc:title": "Some Code List Catalog Record",
              "rdfs:label": "Some Code List Catalog Record",
              "dc:issued": {
                  "@type": "dateTime"
              },
              "dc:modified": {
                  "@type": "dateTime"
              },
              "http://publishmydata.com/pmdcat#metadataGraph": {
                  "@id": "http://some.id"
              }
          }
        ]
      }
      """


    Scenario: Creating New Global Level Metadata File from CSV.
    Given We have a CSV file named "my-favourite-code-list.csv" with headers
      """
      Label,Notation,Parent Notation,Sort Priority,Description
      """
    When We generate a CSVW metadata file at the global level
    Then The following properties are set
      """
        {
            "@context": "http://www.w3.org/ns/csvw",
            "@id": "http://gss-data.org.uk/def/concept-scheme/my-favourite-code-list",
            "url": "my-favourite-code-list.csv",
            "rdfs:label": "My Favourite Code List",
            "dc:title": "My Favourite Code List",
            "tableSchema": {
                "columns": [
                    {
                        "titles": "Label",
                        "name": "label",
                        "datatype": "string",
                        "required": true,
                        "propertyUrl": "rdfs:label"
                    },
                    {
                        "titles": "Notation",
                        "name": "notation",
                        "datatype": {
                            "base": "string",
                            "format": "^-?[\\w\\.\\/\\+]+(-[\\w\\.\\/\\+]+)*$"
                        },
                        "required": true,
                        "propertyUrl": "skos:notation"
                    },
                    {
                        "titles": "Parent Notation",
                        "name": "parent_notation",
                        "datatype": {
                            "base": "string",
                            "format": "^(-?[\\w\\.\\/\\+]+(-[\\w\\.\\/\\+]+)*|)$"
                        },
                        "required": false,
                        "propertyUrl": "skos:broader",
                        "valueUrl": "http://gss-data.org.uk/def/concept-scheme/my-favourite-code-list/{parent_notation}"
                    },
                    {
                        "titles": "Sort Priority",
                        "name": "sort_priority",
                        "datatype": "integer",
                        "required": false,
                        "propertyUrl": "http://www.w3.org/ns/ui#sortPriority"
                    },
                    {
                        "titles": "Description",
                        "name": "description",
                        "datatype": "string",
                        "required": false,
                        "propertyUrl": "rdfs:comment"
                    },
                    {
                        "virtual": true,
                        "propertyUrl": "rdf:type",
                        "valueUrl": "skos:Concept"
                    },
                    {
                        "virtual": true,
                        "propertyUrl": "skos:inScheme",
                        "valueUrl": "http://gss-data.org.uk/def/concept-scheme/my-favourite-code-list"
                    }
                ],
                "primaryKey": "notation",
                "aboutUrl": "http://gss-data.org.uk/def/concept-scheme/my-favourite-code-list/{notation}"
            },
            "prov:hadDerivation": {
                "@id": "http://gss-data.org.uk/def/concept-scheme/my-favourite-code-list",
                "@type": [
                    "skos:ConceptScheme",
                    "http://publishmydata.com/pmdcat#DatasetContents"
                ]
            }
        }
      """

    Scenario: Creating New Family Level Metadata File from CSV. N.B. Family Level URIs.
    Given We have a CSV file named "my-favourite-code-list.csv" with headers
      """
      Label,Notation,Parent Notation,Sort Priority,Description
      """
    Given The code list is in the "My Favourite Family" family
    When We generate a CSVW metadata file at the family level
    Then The following properties are set
      """
        {
            "@id": "http://gss-data.org.uk/def/my-favourite-family/concept-scheme/my-favourite-code-list",
            "tableSchema": {
                "columns": [
                    {
                        "propertyUrl": "skos:broader",
                        "valueUrl": "http://gss-data.org.uk/def/my-favourite-family/concept-scheme/my-favourite-code-list/{parent_notation}"
                    },
                    {
                        "propertyUrl": "skos:inScheme",
                        "valueUrl": "http://gss-data.org.uk/def/my-favourite-family/concept-scheme/my-favourite-code-list"
                    }
                ],
                "aboutUrl": "http://gss-data.org.uk/def/my-favourite-family/concept-scheme/my-favourite-code-list/{notation}"
            },
            "prov:hadDerivation": {
                "@id": "http://gss-data.org.uk/def/my-favourite-family/concept-scheme/my-favourite-code-list"
            }
        }
      """

    Scenario: Creating New Metadata File at the dataset level from CSV. N.B. Distinct dataset #scheme/ & #concept/ URIs.
    Given We have a CSV file named "my-favourite-code-list.csv" with headers
      """
      Label,Notation,Parent Notation,Sort Priority,Description
      """
    And We have an info json config of the form
      """
      {
        "title": "The Best Dataset Ever"
      }
      """
    Given The code list is in the "My Favourite Family" family
    When We generate a CSVW metadata file at the dataset level
    Then The following properties are set
      """
        {
            "@id": "http://gss-data.org.uk/data/gss_data/my-favourite-family/the-best-dataset-ever#scheme/my-favourite-code-list",
            "tableSchema": {
                "columns": [
                    {
                        "propertyUrl": "skos:broader",
                        "valueUrl": "http://gss-data.org.uk/data/gss_data/my-favourite-family/the-best-dataset-ever#concept/my-favourite-code-list/{parent_notation}"
                    },
                    {
                        "propertyUrl": "skos:inScheme",
                        "valueUrl": "http://gss-data.org.uk/data/gss_data/my-favourite-family/the-best-dataset-ever#scheme/my-favourite-code-list"
                    }
                ],
                "aboutUrl": "http://gss-data.org.uk/data/gss_data/my-favourite-family/the-best-dataset-ever#concept/my-favourite-code-list/{notation}"
            },
            "prov:hadDerivation": {
                "@id": "http://gss-data.org.uk/data/gss_data/my-favourite-family/the-best-dataset-ever#scheme/my-favourite-code-list"
            }
        }
      """

Scenario: Creating New Global Level Metadata File from CSV with atypical column names.
    Given We have a CSV file named "my-favourite-code-list.csv" with headers
      """
      Some Column Name,Some Other Column Name
      """
    When We generate a CSVW metadata file at the global level
    Then The following properties are set
      """
        {
            "tableSchema": {
                "columns": [
                    {
                        "titles": "Some Column Name",
                        "name": "some_column_name"
                    },
                    {
                        "titles": "Some Other Column Name",
                        "name": "some_other_column_name"
                    },
                    {
                        "virtual": true,
                        "propertyUrl": "rdf:type",
                        "valueUrl": "skos:Concept"
                    },
                    {
                        "virtual": true,
                        "propertyUrl": "skos:inScheme",
                        "valueUrl": "http://gss-data.org.uk/def/concept-scheme/my-favourite-code-list"
                    }
                ]
            }
        }
      """
  And The following properties are not set
    """
    {
      "tableSchema": {
        "primaryKey": true,
        "aboutUrl": true
      }
    }
    """
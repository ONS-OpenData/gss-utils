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


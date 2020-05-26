Feature: Create CWVW metadata
  I want to create CSVW metadata from a simple mapping file.
  I want the CSVW metadata to declare the transformation from CSV to RDF using the Data Cube Vocabulary.
  I want to include dataset definitions and dataset metadata in the CSVW metadata.

  Scenario: Create CSVW metadata from mapping
    Given a CSV file 'product-observations.csv'
      | Value | Marker | Year | Country | Industry | Direction | Commodity |
      | 0.0   |        | 2008 | AD      | 12       | IM        | T         |
      | 0.0   |        | 2009 | AD      | 12       | IM        | T         |
      | 0.0   |        | 2010 | AD      | 12       | IM        | T         |
      | 0.0   |        | 2011 | AD      | 12       | IM        | T         |
    And a JSON map file 'mapping-info.json'
    And a registry at 'http://gss-data.org.uk/sparql'
    When I create a CSVW file from the mapping and CSV
    Then the metadata is valid JSON-LD
    And gsscogs/csv2rdf generates RDF
    And the RDF should pass the Data Cube integrity constraints
    And the RDF should contain
    """
      @base <file:/tmp/product-observations.csv-metadata.json> .
      @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
      @prefix qb:    <http://purl.org/linked-data/cube#> .
      @prefix sdmx-a: <http://purl.org/linked-data/sdmx/2009/attribute#> .
      @prefix sdmx-d: <http://purl.org/linked-data/sdmx/2009/dimension#> .
      @prefix sdmx-c: <http://purl.org/linked-data/sdmx/2009/code#> .
      @prefix gss-dim: <http://gss-data.org.uk/def/dimension/> .
      @prefix gss-meas: <http://gss-data.org.uk/def/measure/> .

      <#dataset> a qb:DataSet ;
              qb:structure <#structure> .

      <#structure> a qb:DataStructureDefinition ;
                qb:component <#component/commodity>, <#component/country> .
    """

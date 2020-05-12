Feature: Create CWVW metadata
  I want to create CSVW metadata from a simple mapping file.
  I want the CSVW metadata to declare the transformation from CSV to RDF using the Data Cube Vocabulary.
  I want to include dataset definitions and dataset metadata in the CSVW metadata.

  Scenario: Create CSVW metadata from mapping
    Given a CSV file 'product-observations.csv'
      | period    | country | product | direction | basis | unit | adjustment | value |
      | year/1998 | estonia | T       | exports   | bop   | cp   | sa         | 39    |
      | year/1999 | estonia | T       | exports   | bop   | cp   | sa         | 24    |
      | year/2000 | estonia | T       | exports   | bop   | cp   | sa         | 35    |
    And a JSON map file 'mapping-info.json'
    When I create a CSVW metadata file 'product-observations.csv-metadata.json' for base 'http://gss-data.org.uk/data/' and path 'gss_data/trade/ons-mrets-products'
    Then the metadata is valid JSON-LD
    And cloudfluff/csv2rdf generates RDF
    And the RDF should contain
    """
      @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
      @prefix qb:    <http://purl.org/linked-data/cube#> .
      @prefix sdmx-a: <http://purl.org/linked-data/sdmx/2009/attribute#> .
      @prefix sdmx-d: <http://purl.org/linked-data/sdmx/2009/dimension#> .
      @prefix sdmx-c: <http://purl.org/linked-data/sdmx/2009/code#> .
      @prefix gss-dim: <http://gss-data.org.uk/def/dimension/> .
      @prefix gss-meas: <http://gss-data.org.uk/def/measure/> .

      <http://gss-data.org.uk/data/gss_data/trade/ons-mrets-products>
              a             qb:DataSet ;
              qb:structure  <http://gss-data.org.uk/data/gss_data/trade/ons-mrets-products/structure> .
    """

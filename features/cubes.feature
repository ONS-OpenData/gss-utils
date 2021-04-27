Feature: Creating cubes
  As a data engineer.
  I want to scrape metadata and transform spreadsheets into data cubes.
  Data cubes are represented as Tidy CSV and CSV-W metadata.

  Scenario: Output a single PMD4 cube entity
    Given I want to create "PMD4" datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 1" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    Then the datacube outputs can be created
    And the TriG at "out/test-cube-1.csv-metadata.trig" should contain
      """
      @prefix dcat: <http://www.w3.org/ns/dcat#> .
      @prefix dct: <http://purl.org/dc/terms/> .
      @prefix gdp: <http://gss-data.org.uk/def/gdp#> .
      @prefix gov: <https://www.gov.uk/government/organisations/> .
      @prefix pmdcat: <http://publishmydata.com/pmdcat#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix theme: <http://gss-data.org.uk/def/concept/statistics-authority-themes/> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <http://gss-data.org.uk/data/gss_data/trade/ons-quarterly-balance-of-payments-catalog-entry> a pmdcat:Dataset ;
          rdfs:label "Quarterly Balance of Payments"@en ;
          gdp:family gdp:trade ;
          dct:creator gov:office-for-national-statistics ;
          dct:description "Quarterly summary of balance of payments accounts including the current account, capital transfers, transactions and levels of UK external assets and liabilities."@en ;
          dct:issued "2019-12-20"^^xsd:date ;
          dct:publisher gov:office-for-national-statistics ;
          dct:title "Quarterly Balance of Payments"@en ;
          dcat:landingPage <https://www.gov.uk/government/collections/local-alcohol-profiles-for-england-lape> ;
          dcat:theme gdp:trade, gdp:economy .
      """


  Scenario: Output multiple PMD4 cube entities
    Given I want to create "PMD4" datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 1" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 2" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 3" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 4" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    Then the datacube outputs can be created


  Scenario: Override of the containing PMD4 Graph URI works
    Given I want to create "PMD4" datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I add a cube "test cube 1" with data "quarterly-balance-of-payments.csv" and a scrape seed "seed-temp-scrape-quarterly-balance-of-payments.json" with override containing graph "http://containing-graph-uri"
    Then the datacube outputs can be created
    Then generate RDF from the n=0 cube's CSV-W output
    And the RDF should contain
    """
    @prefix sd: <http://www.w3.org/ns/sparql-service-description#>.

    <http://containing-graph-uri> a sd:NamedGraph.
    """
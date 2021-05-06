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

  Scenario: Output both a CMD and PMD cube entity
    Given I want to create "PMD4 and CMD" datacubes from the seed "cubes/seed-cmdpmd-ons-quarterly-country-and-regional-gdp.json"
    # TODO - no way we should be defining the seed twice, unpick this
    And I specify a datacube named "test cube 1" with data "cubes/input-pmdcmd-gdp.csv" and a scrape using the seed "cubes/seed-cmdpmd-ons-quarterly-country-and-regional-gdp.json"
    And I attach to datacube "test cube 1" a "CMD" formater named "formater_cmd_example1"
    And I attach to datacube "test cube 1" a "PMD4" formater named "formater_pmd4_example1"
    Then the datacube outputs can be created
    And the "PMD4" output for "test cube 1" matches "cubes/output-pmd-quarterly-country-and-regional-gdp.csv"
    And the "CMD" output for "test cube 1" matches "cubes/output-cmd-regional-gdp-by-year-time-series-v3.csv"

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
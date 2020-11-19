Feature: Creating cubes
  As a data engineer.
  I want to scrape metadata and transform spreadsheets into data cubes.
  Data cubes are represented as Tidy CSV and CSV-W metadata.

  Scenario: Output a single cube entity
    Given I want to create datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 1" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    Then the datacube outputs can be created
    # The next one is overlly specific for BDD but necessary while we're still stuck with a .trig file
    And the output metadata references the correct number of namespaces

  Scenario: Output multiple cube entities
    Given I want to create datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 1" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 2" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 3" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 4" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    Then the datacube outputs can be created
    # The next one is overlly specific for BDD but necessary while we're still stuck with a .trig file
    And the output metadata references the correct number of namespaces

  Scenario: Output the expected CSV-W metadata schema
    Given I want to create datacubes from the seed "seed-temp-scrape-lsoa.json"
    And I specify a datacube named "Lower Super Output Areas (LSOA) electricity consumption" with data "lower-super-output-areas-lsoa-electricity-consumption.csv" and a scrape using the seed "seed-temp-scrape-lsoa.json"
    Then the csv-w schema for "Lower Super Output Areas (LSOA) electricity consumption" matches "lower-super-output-areas-lsoa-electricity-consumption.csv-metadata.json"

  # NOTE - disabling these until we implement codelist generation
  # Scenario: Output the expected CSV-W and csv for codelists
  #  Given I want to create datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
  #  And I specify a datacube named "Quarterly Balance of Payments" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
  #  Then for the datacube "Quarterly Balance of Payments" the csv codelist "BOP Services" is created which matches "codelist-bop-services.csv"
  #  And for the datacube "Quarterly Balance of Payments" the schema for codelist "BOP Services" is created which matches "codelist-bop-services.csv-metadata.json"
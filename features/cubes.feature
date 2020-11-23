Feature: Creating cubes
  As a data engineer.
  I want to scrape metadata and transform spreadsheets into data cubes.
  Data cubes are represented as Tidy CSV and CSV-W metadata.

  Scenario: Output a single cube entity
    Given I want to create datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 1" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    Then the datacube outputs can be created

  Scenario: Output multiple cube entities
    Given I want to create datacubes from the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 1" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 2" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 3" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    And I specify a datacube named "test cube 4" with data "quarterly-balance-of-payments.csv" and a scrape using the seed "seed-temp-scrape-quarterly-balance-of-payments.json"
    Then the datacube outputs can be created
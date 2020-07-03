Feature: Creating cubes
  As a data engineer.
  I want to scrape metadata and transform spreadsheets into data cubes.
  Data cubes are represented as Tidy CSV and CSV-W metadata.

  Scenario: Create a single cube entity
    Given I want to create datacubes from the seed "seed-for-cube-test-without-mapping.json"
    And I specifiy a datacube named "test cube" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-without-mapping.json"
    Then the datacube outputs can be created
    And the output metadata references the correct number of namespaces

  Scenario: Create multiple cube entities
    Given I want to create datacubes from the seed "seed-for-cube-test-without-mapping.json"
    And I specifiy a datacube named "test cube 1" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-without-mapping.json"
    And I specifiy a datacube named "test cube 2" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-without-mapping.json"
    And I specifiy a datacube named "test cube 3" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-without-mapping.json"
    And I specifiy a datacube named "test cube 4" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-without-mapping.json"
    Then the datacube outputs can be created
    And the output metadata references the correct number of namespaces
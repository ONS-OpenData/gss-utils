Feature: Create datacube entities representing a combination of data and metadata
  In an automated pipeline
  I want to store the data and metadata that describe a datacube as a single entity
  I want to keep a list of all such entities I've created
  I want to use this list of entities to trigger the transformation of the data 

  Scenario: Create a single cube entity
    Given I create a list of datacubes for data family "https://gss-cogs.github.io/family-trade/reference/"
    And I add a datacube named "test cube" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-with-all-data.json"
    # Note - the following step is being called with `with_transform=False` in steps/cube.py, that needs 
    # to be removed once we have the handling for mapping.
    Then the datacube outputs can be created
    And datacube "1" references "1" datacube namspace(s)

  Scenario: Create multiple cube entities
    Given I create a list of datacubes for data family "https://gss-cogs.github.io/family-trade/reference/"
    And I add a datacube named "test cube 1" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-with-all-data.json"
    And I add a datacube named "test cube 2" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-with-all-data.json"
    And I add a datacube named "test cube 3" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-with-all-data.json"
    And I add a datacube named "test cube 4" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-with-all-data.json"
    # Note - the following step is being called with `with_transform=False` in steps/cube.py, that needs 
    # to be removed once we have the handling for mapping.
    Then the datacube outputs can be created
    And datacube "1" references "1" datacube namspace(s)
    And datacube "2" references "2" datacube namspace(s)
    And datacube "3" references "3" datacube namspace(s)
    And datacube "4" references "4" datacube namspace(s)

  # Note - accounting for old pipelines that don't have an info.json to provide "theme", "family" etc
  Scenario: Pass missing metadata to a legacy datacube pipeline
    Given I create a list of datacubes for "https://gss-cogs.github.io/family-trade/reference/" with additional runtime metadata from "cube-runtime-metadata.json"
    And I add a datacube named "test cube" with data "test-data-1.csv" and a scrape using the seed "seed-for-cube-test-with-limited-data.json"
    Then the datacube outputs can be created



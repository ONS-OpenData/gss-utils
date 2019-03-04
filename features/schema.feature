Feature: Manage CSVW schema for validation
  While transforming into Tidy data
  In an automated pipeline
  I want to be able to validate the CSV output using CSVW schema
  The schema can be derived from the CSV and the conventions used by table2qb

  Scenario: Create CSVW schema
    Given table2qb configuration at 'https://ons-opendata.github.io/ref_migration/'
    And a CSV file 'observations.csv'
      | HO Country of Nationality | Period    | Age | Sex | Measure Type | Value | Unit         |
      | africa-north              | year/2008 | all | T   | Count        | 883   | applications |
    When I create a CSVW schema 'schema.json'
    Then The schema is valid JSON
    And cloudfluff/csvlint validates ok
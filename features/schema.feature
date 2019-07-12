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
    Then the schema is valid JSON
    And cloudfluff/csvlint validates ok

  @skip
  Scenario: Cope with data markers
    Given table2qb configuration at 'https://ons-opendata.github.io/ref_migration/'
    And a CSV file 'observations.csv'
      | Year | Country of Residence | Migration Flow | IPS Citizenship | Sex | Age     | Measure Type | Value | IPS Marker | CI  | Unit             |
      | 2017 | south-asia           | inflow         | all             | T   | agq/0-4 | Count        | 1.7   |            | 1.5 | people-thousands |
      | 2017 | south-east-asia      | inflow         | all             | T   | agq/0-4 | Count        |       | no-contact | .   | people-thousands |
    When I create a CSVW schema 'schema.json'
    Then the schema is valid JSON
    And cloudfluff/csvlint validates ok

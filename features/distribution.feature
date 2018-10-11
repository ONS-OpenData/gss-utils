Feature: distribution downloading

  Scenario: databaker
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    And fetch the distribution as a databaker object
    Then the sheet names contain [Contents, 1.1, 1.2, 1.3, Geography, SIC]
    And I can access excel_ref 'A4' in the '1.1' tab

  Scenario: databaker with nrscotland XLSX
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-between-scotland-and-overseas"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.ms-excel                                   |
      | title     | Migration between administrative areas and overseas by sex |
    And fetch the distribution as a databaker object
    Then the sheet names contain [Contents, Metadata, Net-Council Area-Sex]
    And I can access excel_ref 'B6' in the 'Net-Council Area-Sex' tab

  Scenario: pandas with nrscotland XLSX
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-between-scotland-and-overseas"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.ms-excel                                   |
      | title     | Migration between Scotland and overseas by age             |
    And fetch the 'SYOA Females (2001-)' tab as a pandas DataFrame
    Then the dataframe should have 62 rows

  Scenario: databaker from ODS
    Given I scrape the page "https://www.gov.uk/government/statistics/national-insurance-number-allocations-to-adult-overseas-nationals-to-march-2018"
    And select the distribution given by
      | key       | value                                                                                           |
      | mediaType | application/vnd.oasis.opendocument.spreadsheet                                                  |
      | title     | Summary tables: National Insurance number allocations to adult overseas nationals to March 2018 |
    And fetch the distribution as a databaker object
    Then the sheet names contain [CONTENTS, 1, 2, 3, 4]

  Scenario: Select ditribution by start of title
    Given I scrape the page "https://www.nisra.gov.uk/publications/2017-mid-year-population-estimates-northern-ireland-new-format-tables"
    Then select the distribution whose title starts with "Northern Ireland - Migration flows by type"

  Scenario: ONS distributions with no titles
    Given I scrape the page "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/migrationwithintheuk/datasets/localareamigrationindicatorsunitedkingdom"
    Then select the distribution whose title starts with "Local area migration indicators"
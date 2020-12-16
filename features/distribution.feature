Feature: distribution downloading

  Scenario: databaker
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    And fetch the distribution as a databaker object
    Then the sheet names contain [Contents, 1.1, 1.2, 1.3, Geography, SIC]
    And I can access excel_ref 'A4' in the '1.1' tab

  Scenario: databaker with nrscotland XLSX
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-flows/migration-between-scotland-and-overseas"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.ms-excel                                   |
      | title     | Migration between administrative areas and overseas by sex |
    And fetch the distribution as a databaker object
    Then the sheet names contain [Contents, Metadata, Net-Council Area-Sex]
    And I can access excel_ref 'B6' in the 'Net-Council Area-Sex' tab

  Scenario: pandas with nrscotland XLSX
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-flows/migration-between-scotland-and-overseas"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.ms-excel                                   |
      | title     | Migration between Scotland and overseas by age             |
    And fetch the 'SYOA Females (2001-)' tab as a pandas DataFrame
    Then the dataframe should have 73 rows

  Scenario: databaker from ODS
    Given I scrape the page "https://www.gov.uk/government/statistics/national-insurance-number-allocations-to-adult-overseas-nationals-to-march-2018"
    And select the distribution given by
      | key       | value                                                                                           |
      | mediaType | application/vnd.oasis.opendocument.spreadsheet                                                  |
      | title     | Summary tables: National Insurance number allocations to adult overseas nationals to March 2018 |
    And fetch the distribution as a databaker object
    Then the sheet names contain [CONTENTS, 1, 2, 3, 4]

  Scenario: Select distribution by start of title
    Given I scrape the page "https://www.nisra.gov.uk/publications/2017-mid-year-population-estimates-northern-ireland-new-format-tables"
    Then select the distribution whose title starts with "Northern Ireland - Migration flows by type"

  Scenario: ONS distributions with no titles
    Given I scrape the page "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/migrationwithintheuk/datasets/localareamigrationindicatorsunitedkingdom"
    Then select the distribution whose title starts with "Local area migration indicators"

  Scenario: Home Office ODS tab as Pandas DataFrame
    Given I scrape the page "https://www.gov.uk/government/statistics/immigration-statistics-october-to-december-2017-data-tables"
    And select the distribution whose title starts with "Entry clearance visas granted outside the UK data tables immigration statistics October to December 2017 volume 1"
    And fetch the 'vi_05' tab as a pandas DataFrame

  Scenario: Home Office ODS tabs as dict of Pandas DataFrames
    Given I scrape the page "https://www.gov.uk/government/statistics/immigration-statistics-october-to-december-2017-data-tables"
    And select the distribution whose title starts with "Entry clearance visas granted outside the UK data tables immigration statistics October to December 2017 volume 1"
    Then fetch the tabs as a dict of pandas DataFrames

  Scenario: DfT statistics data set
    Given I scrape the page "https://www.gov.uk/government/statistical-data-sets/ras51-reported-drinking-and-driving"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Drink-drive accidents and casualties"
    And select the distribution whose title starts with "Reported drink drive accidents and casualties in Great Britain since 1979"
    Then fetch the 'RAS51001' tab as a pandas DataFrame

  Scenario: DfT statistics data set including Excel
    Given I scrape the page "https://www.gov.uk/government/statistical-data-sets/ras45-quarterly-statistics"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Latest rolling annual total"
    And select the distribution given by
      | key       | value                                                                                                      |
      | mediaType | application/vnd.oasis.opendocument.spreadsheet                                                             |
      | title     | Reported road accidents, by road type (estimates): Great Britain, rolling annual totals, updated quarterly |
    Then the data can be downloaded from "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/588103/ras45009.ods"
    
  Scenario: NI DoJ Excel data as DataBaker
    Given I scrape the page "https://www.justice-ni.gov.uk/publications/research-and-statistical-bulletin-82017-views-alcohol-and-drug-related-issues-findings-october-2016"
    And select the distribution whose title starts with "October 2016 alcohol and drugs findings data table"
    And fetch the distribution as a databaker object
    Then the sheet names contain [Metadata, Table A1]

  Scenario: StatsWales OData API
    Given I scrape the page "https://statswales.gov.wales/Catalogue/Housing/Dwelling-Stock-Estimates/dwellingstockestimates-by-localauthority-tenure"
    And select the distribution whose title starts with "Dataset"
    Then the data can be downloaded from "http://open.statswales.gov.wales/dataset/hous0501"
    And fetch the distribution as a pandas dataframe
    And the dataframe should have 2725 rows

  Scenario: StatsWales OData API codelists URL without spaces
    Given I scrape the page "https://statswales.gov.wales/Catalogue/Housing/Dwelling-Stock-Estimates/dwellingstockestimates-by-localauthority-tenure"
    And select the distribution whose title starts with "Items"
    Then the data can be downloaded from "http://open.statswales.gov.wales/en-gb/discover/datasetdimensionitems?$filter=Dataset+eq+'hous0501'"
    
  Scenario: NHS Digital Open data CSV
    Given I scrape the page "https://digital.nhs.uk/data-and-information/publications/statistical/adult-social-care-outcomes-framework-ascof"
    When I select the latest dataset whose title starts with "Measures"
    And select the distribution given by
      | key       | value    |
      | mediaType | text/csv |
    And fetch the distribution as a pandas dataframe with encoding "Windows-1252"
    Then the dataframe should have 75648 rows

  Scenario: ODS conversion has bad tab name
    Given I scrape the page "https://www.gov.uk/government/statistics/alcohol-bulletin"
    And select the distribution given by
      | key       | value                                            |
      | mediaType | application/vnd.oasis.opendocument.spreadsheet   |
      | title     | Alcohol Bulletin tables (August to October 2020) |
    And fetch the distribution as a databaker object
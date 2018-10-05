Feature: distribution downloading

  Scenario: databaker
    Given a dataset page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    When I scrape this page
    And fetch the distribution as a databaker object
    Then the sheet names contain [Contents, 1.1, 1.2, 1.3, Geography, SIC]
    And I can access excel_ref 'A4' in the '1.1' tab

  Scenario: databaker with nrscotland XLSX
    Given a dataset page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-between-scotland-and-overseas"
    When I scrape this page
    And select "XLSX" files
    And select files with title "Migration between administrative areas and overseas by sex"
    And fetch the distribution as a databaker object
    Then the sheet names contain [Contents, Metadata, Net-Council Area-Sex]
    And I can access excel_ref 'B6' in the 'Net-Council Area-Sex' tab
Feature: distribution downloading

  Scenario: databaker
    Given a dataset page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    When I scrape this page
    And fetch the distribution as a databaker object
    Then the sheet names are [Contents, 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, Geography, SIC]
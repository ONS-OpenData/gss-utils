Feature: Scrape dataset info
  In an automated pipeline
  I want to gather metadata about published data from a web page,
  including the location to fetch the data from.

  Scenario: Scrape ONS
    Given a dataset page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    When I scrape this page
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables/current/annualforeigndirectinvestmentinward2016.xls"
    And the title should be "Foreign direct investment involving UK companies: Inward tables"
    And the publication date should be "2017-12-01"
    And the next release date should be "2018-12-03"
    And the description should read "Inward datasets including data for flows, positions and earnings."
    And the contact email address should be "mailto:fdi@ons.gov.uk"
Feature: Scrape dataset info
  In an automated pipeline
  I want to gather metadata about published data from a web page,
  including the location to fetch the data from.

  Scenario: Scrape ONS
    Given a dataset page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    When I scrape this page
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables/current/annualforeigndirectinvestmentinward2016.xls"
Feature: Scrape dataset info
  In an automated pipeline
  I want to gather initial information about published data from a web page,
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

  Scenario: ONS metadata profile
    Given a dataset page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    When I scrape this page
    Then dct:title should be `"Foreign direct investment involving UK companies: Inward tables"@en`
    And dct:description should be `"Inward datasets including data for flows, positions and earnings."@en`
    And dct:publisher should be `gov:office-for-national-statistics`
    And dct:issued should be `"2017-12-01"^^xsd:date`
    And dcat:contactPoint should be `<mailto:fdi@ons.gov.uk>`

  Scenario: Scrape gov.uk template
    Given a dataset page "https://www.gov.uk/government/statistics/immigration-statistics-october-to-december-2017-data-tables"
    When I scrape this page
    And select "ODS" files
    And select files with title "Entry clearance visas granted outside the UK data tables immigration statistics October to December 2017 volume 1"
    Then the data can be downloaded from "https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/683359/entry-visas1-oct-dec-2017-tables.ods"

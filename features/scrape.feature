Feature: Scrape dataset info
  In an automated pipeline
  I want to gather initial information about published data from a web page,
  including the location to fetch the data from.

  Scenario: Scrape ONS
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables/current/annualforeigndirectinvestment2017inward.xls"
    And the title should be "Foreign direct investment involving UK companies: inward"
    And the publication date should be "2018-12-04"
    And the comment should be "Annual statistics on the investment of foreign companies into the UK, including for investment flows, positions and earnings."
    And the contact email address should be "mailto:fdi@ons.gov.uk"

  Scenario: ONS metadata profile
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    Then dct:title should be `"Foreign direct investment involving UK companies: inward"@en`
    And rdfs:comment should be `"Annual statistics on the investment of foreign companies into the UK, including for investment flows, positions and earnings."@en`
    And dct:publisher should be `gov:office-for-national-statistics`
    And dct:issued should be `"2018-12-04"^^xsd:date`
    And dcat:contactPoint should be `<mailto:fdi@ons.gov.uk>`

  Scenario: Scrape gov.uk template
    Given I scrape the page "https://www.gov.uk/government/statistics/immigration-statistics-october-to-december-2017-data-tables"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.oasis.opendocument.spreadsheet             |
      | title     | Entry clearance visas granted outside the UK data tables immigration statistics October to December 2017 volume 1 |
    Then the data can be downloaded from "https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/683359/entry-visas1-oct-dec-2017-tables.ods"

  Scenario: Scrape nrscotland
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-flows/migration-between-scotland-and-overseas"
    Then the title should be "Migration between Scotland and Overseas"
    And the description should start "Migration between Scotland and overseas refers to people moving between"

  Scenario: nrscotland downloads
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-flows/migration-between-scotland-and-overseas"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.ms-excel                                   |
      | title     | Migration between administrative areas and overseas by sex |
    Then the data can be downloaded from "https://www.nrscotland.gov.uk/files//statistics/migration/flows/apr-19/mig-overseas-admin-sex-tab1.xlsx"

  Scenario: Scrape NISRA
    Given I scrape the page "https://www.nisra.gov.uk/publications/2017-mid-year-population-estimates-northern-ireland-new-format-tables"
    Then the title should be "2017 Mid Year Population Estimates for Northern Ireland (NEW FORMAT TABLES)"
    And dct:issued should be `"2018-06-28"^^xsd:date`
    And dcat:keyword should be `"Population, Mid Year Population Estimates"@en`
    And dct:publisher should be `gov:northern-ireland-statistics-and-research-agency`
    And select the distribution given by
      | key       | value                                       |
      | mediaType | application/vnd.ms-excel                    |
      | title     | All areas - Components of population change |
    And the data can be downloaded from "https://www.nisra.gov.uk/sites/nisra.gov.uk/files/publications/MYE17_CoC.xlsx"
    
  Scenario: Scrape HMRC
    Given I scrape the page "https://www.uktradeinfo.com/Statistics/Pages/TaxAndDutybulletins.aspx"
    And the catalog has more than one dataset
    When I select the dataset "Alcohol Duty"
    Then the data can be downloaded from "https://www.uktradeinfo.com/Statistics/Tax%20and%20Duty%20Bulletins/Alcohol0419.xls"

  Scenario: Scrape gov.uk statistical-data-sets
    Given I scrape the page "https://www.gov.uk/government/statistical-data-sets/ras51-reported-drinking-and-driving"
    Then the title should be "Reported drinking and driving (RAS51)"
    And the publication date should be "2014-02-06"
    And the comment should be "Data about the reported drink-drive accidents and casualties, produced by Department for Transport."
    And the contact email address should be "mailto:roadacc.stats@dft.gov.uk"
    And dct:publisher should be `gov:department-for-transport`

  Scenario: Scrape NI DoJ
    Given I scrape the page "https://www.justice-ni.gov.uk/publications/research-and-statistical-bulletin-82017-views-alcohol-and-drug-related-issues-findings-october-2016"
    Then the title should be "Research and Statistical Bulletin 8/2017 ‘Views on Alcohol and Drug Related Issues: Findings from the October 2016 Northern Ireland Omnibus Survey’"
    And the publication date should be "2017-03-08"

  Scenario: Scrape ISD Scotland
    Given I scrape the page "http://www.isdscotland.org/Health-Topics/Drugs-and-Alcohol-Misuse/Publications/"
    And the catalog has more than one dataset
    When I select the dataset "National Drug and Alcohol Treatment Waiting Times"
    Then the title should be "National Drug and Alcohol Treatment Waiting Times"
    And dct:publisher should be `gov:information-services-division-scotland`

  Scenario: Scrape uktradeinfo OTSReports
    Given I scrape the page "https://www.uktradeinfo.com/Statistics/OverseasTradeStatistics/AboutOverseastradeStatistics/Pages/OTSReports.aspx"
    And the catalog has more than one dataset
    When I select the dataset whose title starts with "UK Trade in Goods by Business Characteristics"

  Scenario: Scrape ONS User Requested Data
    Given I scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/adhocs/008596individualcountrydatagoodsonamonthlybasisfromjanuary1998toapril2018"
    Then the title should be "Individual country data (goods) on a monthly basis from January 1998 to April 2018"
    And the comment should be "Exports and imports goods data by individual country for UK trade in goods."
    And the data can be downloaded from "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/adhocs/008596individualcountrydatagoodsonamonthlybasisfromjanuary1998toapril2018/04.allcountriesapril2018.xls"

  Scenario: Scrape DoH Northern Ireland
    Given I scrape the page "https://www.health-ni.gov.uk/publications/census-drug-and-alcohol-treatment-services-northern-ireland-2017"
    Then dct:publisher should be `gov:department-of-health-northern-ireland`

  Scenario: Scrape gov.uk collection
    Given I scrape the page "https://www.gov.uk/government/collections/national-insurance-number-allocations-to-adult-overseas-nationals-entering-the-uk"
    And the catalog has more than one dataset
    When I select the dataset whose title starts with "National Insurance number allocations to adult overseas nationals to September 2018"
    Then dct:title should be `"National Insurance number allocations to adult overseas nationals to September 2018"@en`
    And dct:publisher should be `gov:department-for-work-pensions`

  Scenario: Cope with bad mailto URIs
    Given I scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet"
    Then the title should be "UK trade time series"
    And dcat:contactPoint should be `<mailto:trade@ons.gov.uk>`

  Scenario: Scrape HMRC RTS downloads page
    Given I scrape the page "https://www.uktradeinfo.com/Statistics/RTS/Pages/default.aspx"
    Then the title should be "UK Regional Trade Statistics (RTS"
    And the contact email address should be "mailto:uktradeinfo@hmrc.gsi.gov.uk"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/zip                                            |
      | title     | RTS 2017                                                   |
    Then the data can be downloaded from "https://www.uktradeinfo.com/Statistics/RTS/Documents/Rtsweb%202017.zip"

  Scenario: Get media type right
    Given I scrape the page "https://www.gov.uk/government/statistics/regional-trade-in-goods-statistics-dis-aggregated-by-smaller-geographical-areas-2017"
    And select the distribution given by
      | key       | value                                                                                            |
      | mediaType | application/vnd.ms-excel                                                                         |
      | title     | Regional trade in goods statistics disaggregated by smaller geographical areas: Data Tables 2017 |
    Then the data can be downloaded from "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/763405/Local_Area_Tables_2017.xls"

  Scenario: Scrape another gov.uk collection
    Given I scrape the page "https://www.gov.uk/government/collections/alcohol-and-drug-misuse-and-treatment-statistics"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Substance misuse treatment for adults"
    Then dct:title should be `"Substance misuse treatment for adults: statistics 2017 to 2018"@en`
    And dct:publisher should be `gov:public-health-england`

  Scenario: Scrape NHS digital
    Given I scrape the page "https://digital.nhs.uk/data-and-information/publications/statistical/statistics-on-alcohol"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Statistics on Alcohol, England"
    Then dct:title should be `"Statistics on Alcohol, England 2019 [PAS]"@en`
    And dct:publisher should be `gov:nhs-digital`

  Scenario: Scrape PHE fingertips reference via gov.uk collection
    Given I scrape the page "https://www.gov.uk/government/collections/local-alcohol-profiles-for-england-lape"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Local Alcohol Profiles"
    Then dct:title should be `"Local Alcohol Profiles for England: May 2019 data update"@en`
    And dct:publisher should be `gov:public-health-england`

  Scenario: Scrape StatsWales OData
    Given I scrape the page "https://statswales.gov.wales/Catalogue/Housing/Dwelling-Stock-Estimates/dwellingstockestimates-by-localauthority-tenure"
    Then dct:title should be `"Dwelling Stock Estimates"@en`
    And rdfs:comment should be `"Estimates of the number of dwellings in Wales by tenure and for each local authority, as at 31 March each year."@en`
    And dct:publisher should be `gov:welsh-government`
    And dct:issued should be `"2018-04-26"^^xsd:date`
    And dct:license should be `<http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>`

  Scenario: Scrape old gov.scot dataset page
    Given I scrape the page "https://www2.gov.scot/Topics/Statistics/Browse/Housing-Regeneration/HSfS/KeyInfoTables"
    Then dct:title should be `"Stock by tenure"@en`
    And the data can be downloaded from "https://www2.gov.scot/Resource/0054/00540622.xls"
    And dct:publisher should be `gov:the-scottish-government`
    And dct:issued should be `"2018-09-21"^^xsd:date`

  Scenario: ONS MRETS as csv, xlsx and structured text
    Given I scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet"
    And select the distribution given by
      | key       | value                                                                    |
      | mediaType | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet        |
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet/current/mret.xlsx"
    And select the distribution given by
      | key       | value                           |
      | mediaType | text/csv                        |
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet/current/mret.csv"
    And select the distribution given by
      | key       | value                           |
      | mediaType | text/prs.ons+csdb               |
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet/current/mret.csdb"
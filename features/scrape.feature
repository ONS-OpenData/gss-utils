Feature: Scrape dataset info
  In an automated pipeline
  I want to gather initial information about published data from a web page,
  including the location to fetch the data from.

  Scenario: Scrape ONS
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    And the title should be "Foreign direct investment involving UK companies: inward"
    And the publication date should match "20[0-9]{2}-[01][0-9]-[0-3][0-9]"
    And the comment should be "Annual statistics on the investment of foreign companies into the UK, including for investment flows, positions and earnings."
    And the contact email address should be "mailto:fdi@ons.gov.uk"

  Scenario: ONS metadata profile
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    Then dct:title should be `"Foreign direct investment involving UK companies: inward"@en`
    And rdfs:comment should be `"Annual statistics on the investment of foreign companies into the UK, including for investment flows, positions and earnings."@en`
    And dct:publisher should be `gov:office-for-national-statistics`
    And dct:issued should match `"20[0-9]{2}-[01][0-9]-[0-3][0-9]"\^\^xsd:date`
    And dcat:contactPoint should be `<mailto:fdi@ons.gov.uk>`

  Scenario: Scrape gov.uk template
    Given I scrape the page "https://www.gov.uk/government/statistics/immigration-statistics-october-to-december-2017-data-tables"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.oasis.opendocument.spreadsheet             |
      | title     | Entry clearance visas granted outside the UK data tables immigration statistics October to December 2017 volume 1 |
    Then the data can be downloaded from "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/683359/entry-visas1-oct-dec-2017-tables.ods"

  Scenario: Scrape nrscotland
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-flows/migration-between-scotland-and-overseas"
    Then the title should be "Migration between Scotland and Overseas"
    And the description should start "Migration between Scotland and overseas refers to people moving between"

  Scenario: Scrape nrscotland COVID19
    Given I scrape the page "https://www.nrscotland.gov.uk/covid19stats"
    Then dct:title should be `"Deaths involving coronavirus (COVID-19) in Scotland"@en`
    And the data download URL should match "https://www.nrscotland.gov.uk/files//statistics/.*\.xlsx"
    And dct:publisher should be `gov:national-records-of-scotland`

  Scenario: nrscotland downloads
    Given I scrape the page "https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/migration/migration-statistics/migration-flows/migration-between-scotland-and-overseas"
    And select the distribution given by
      | key       | value                                                      |
      | mediaType | application/vnd.ms-excel                                   |
      | title     | Migration between administrative areas and overseas by sex |
    Then the data can be downloaded from "https://www.nrscotland.gov.uk/files//statistics/migration/flows/apr-20/mig-overseas-admin-sex-tab1.xlsx"

  Scenario: Scrape NISRA
    Given I scrape the page "https://www.nisra.gov.uk/publications/2017-mid-year-population-estimates-northern-ireland-new-format-tables"
    Then the title should be "2017 Mid Year Population Estimates for Northern Ireland (NEW FORMAT TABLES)"
    And dct:issued should match `"20[0-9]{2}-[01][0-9]-[0-3][0-9]"\^\^xsd:date`
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
    And the catalog has more than one dataset
    When I select the dataset "Drink-drive accidents and casualties"
    And select the distribution given by
      | key       | value                                                                     |
      | mediaType | application/vnd.oasis.opendocument.spreadsheet                            |
      | title     | Reported drink drive accidents and casualties in Great Britain since 1979 |
    Then the data can be downloaded from "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/912044/ras51001.ods"
    And dct:description should match `"Data about the reported drink drive accidents and casualties.*`
    And the contact email address should be "mailto:roadacc.stats@dft.gov.uk"
    And dct:publisher should be `gov:department-for-transport`

  Scenario: Scrape NI DoJ
    Given I scrape the page "https://www.justice-ni.gov.uk/publications/research-and-statistical-bulletin-82017-views-alcohol-and-drug-related-issues-findings-october-2016"
    Then the title should be "Research and Statistical Bulletin 8/2017 ‘Views on Alcohol and Drug Related Issues: Findings from the October 2016 Northern Ireland Omnibus Survey’"
    And the publication date should match "20[0-9]{2}-[01][0-9]-[0-3][0-9]"

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
    Then the title should match "Individual country data \(goods\) on a monthly basis.*"
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

  Scenario: Scrape DCNI
    Given I scrape the page "https://www.communities-ni.gov.uk/publications/topic/8182?search=Northern+Ireland+Housing+Statistics+Owner+Occupier+Demand&sort_by=field_published_date"
    And select the distribution given by
      | key       | value                                       |
      | mediaType | application/vnd.ms-excel                    |
    Then dct:publisher should be `gov:department-for-communities-northern-ireland`
    And the publication date should match "20[0-9]{2}-[01][0-9]-[0-3][0-9]"
    And the data download URL should match "^https://www.communities-ni.gov.uk/.*[xX][lL][sS][xX]$"

  Scenario: Cope with bad mailto URIs
    Given I scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet"
    Then the title should be "UK trade time series"
    And dcat:contactPoint should be `<mailto:trade@ons.gov.uk>`

  @skip
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
    Then dct:title should match `"Substance misuse treatment for adults: statistics.*"@en`
    And dct:publisher should be `gov:public-health-england`
    And dct:description should match `.*alcohol and drug misuse treatment for adults from Public Health England's National Drug Treatment Monitoring System.*`

  Scenario: Scrape NHS digital
    Given I scrape the page "https://digital.nhs.uk/data-and-information/publications/statistical/statistics-on-alcohol"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Statistics on Alcohol, England"
    Then dct:title should match `"Statistics on Alcohol, England.*"@en`
    And dct:publisher should be `gov:nhs-digital`

  Scenario: Scrape PHE fingertips reference via gov.uk collection
    Given I scrape the page "https://www.gov.uk/government/collections/local-alcohol-profiles-for-england-lape"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Local Alcohol Profiles"
    Then dct:title should match `"Local Alcohol Profiles for England.*"@en`
    And dct:publisher should be `gov:public-health-england`

  Scenario: Scrape StatsWales OData
    Given I scrape the page "https://statswales.gov.wales/Catalogue/Housing/Dwelling-Stock-Estimates/dwellingstockestimates-by-localauthority-tenure"
    Then dct:title should be `"Dwelling Stock Estimates"@en`
    And rdfs:comment should be `"Estimates of the number of dwellings in Wales by tenure and for each local authority, as at 31 March each year."@en`
    And dct:publisher should be `gov:welsh-government`
    And dct:issued should match `"20[0-9]{2}-[01][0-9]-[0-3][0-9]"\^\^xsd:date`
    And dct:license should be `<http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>`

  # Turning this off, it's just getting redirected to the other scots gov handler
  @skip
  Scenario: Scrape old gov.scot dataset page
    Given I scrape the page "https://www2.gov.scot/Topics/Statistics/Browse/Housing-Regeneration/HSfS/KeyInfoTables"
    Then dct:title should be `"Housing statistics: Stock by tenure"@en`
    And the data download URL should match "https://www\.gov.*\.xls"
    And dct:publisher should be `gov:the-scottish-government`
    And dct:issued should match `"[1-2][0-9][0-9]{2}-[01][0-9]-[0-3][0-9]"\^\^xsd:date`

  Scenario: Scrape new gov.scot dataset page
    Given I scrape the page "https://www.gov.scot/publications/scottish-index-of-multiple-deprivation-2020v2-ranks/"
    Then dct:title should be `"Scottish Index of Multiple Deprivation 2020v2 - ranks"@en`
    And the data download URL should match "https://www\.gov\.scot/binaries/.*\.xlsx"
    And dct:publisher should be `gov:the-scottish-government`
    And dct:issued should match `"20[0-9]{2}-[01][0-9]-[0-3][0-9]"\^\^xsd:date`

  Scenario: Scrape gov.scot collection
    Given I scrape the page "https://www.gov.scot/collections/homelessness-statistics/"
    Then there should be "60" distributions

  Scenario: ONS MRETS as csv, xlsx and structured text
    Given I scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet"
    And select the distribution given by
      | key       | value                                                                    |
      | mediaType | application/vnd.ms-excel        |
      | latest    | true                            |
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet/current/mret.xlsx"
    And select the distribution given by
      | key       | value                           |
      | mediaType | text/csv                        |
      | latest    | true                            |
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet/current/mret.csv"
    And select the distribution given by
      | key       | value                           |
      | mediaType | text/prs.ons+csdb               |
      | latest    | true                            |
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/datasets/tradeingoodsmretsallbopeu2013timeseriesspreadsheet/current/mret.csdb"

  Scenario: NHS Digital collection select latest
    Given I scrape the page "https://digital.nhs.uk/data-and-information/publications/statistical/adult-social-care-outcomes-framework-ascof"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Measures"
    Then dct:title should match `"Measures from the Adult Social Care Outcomes Framework, England.*"@en`

  Scenario: MCHLG live tables from gov.uk
    Given I scrape the page "https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants"
    And select the distribution whose title starts with "Table 100:"
    Then the data can be downloaded from "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/887050/LT_100v2.xls"

  Scenario: MCHLG LA housing stats from gov.uk
    Given I scrape the page "https://www.gov.uk/government/statistical-data-sets/local-authority-housing-statistics-data-returns-for-2018-to-2019"
    When I select the latest dataset whose title starts with "Local"
    Then dct:title should be `"Local authority housing statistics data returns for 2018 to 2019"@en`

  Scenario: Replace missing metadata using a seed
    Given I use the testing seed "seed-with-missing-metadata.json"
    Then the title should be "I am the missing title of a thing"
    And the description should start "I am the missing description of a thing"

  Scenario: Create scrape using only a metadata seed
    Given I use the testing seed "seed-for-temporary-scraper.json"
    And select the distribution given by
      | key       | value              |
      | mediaType | application/zip    |
    Then the title should be "I am a title from the metadata seed"
    And the description should start "I am a description from the metadata seed"
    And the data can be downloaded from "https://www.contextures.com/SampleData.zip"
    And dct:publisher should be `gov:cogs-data-testing`
    And dct:issued should match `"20[0-9]{2}-[01][0-9]-[0-3][0-9]"\^\^xsd:date`

  Scenario: Override scrape metadata using a metadata seed
    Given I use the testing seed "seed-for-metadata-overrides.json"
    Then dct:title should match `"I did override a thing"@en`

  Scenario: gov.uk descriptions
    Given I scrape the page "https://www.gov.uk/government/collections/uk-regional-trade-in-goods-statistics-disaggregated-by-smaller-geographical-areas"
    And the catalog has more than one dataset
    When I select the latest dataset whose title starts with "Regional trade in goods statistics disaggregated by smaller geographical areas"
    Then the description should start "International trade in goods data at summary product and country level, by UK areas smaller than NUTS1"

  Scenario: latest distribution but no issued date
    Given I scrape the page "https://www.gov.uk/government/statistics/alcohol-bulletin"
    And select the distribution whose title starts with "Alcohol Bulletin tables"

  Scenario: gov.uk landing page
    Given I scrape the page "https://www.gov.uk/government/statistics/alcohol-bulletin"
    Then the dataset landing page should be "https://www.gov.uk/government/statistics/alcohol-bulletin"

  Scenario: gov.wales landing page
    Given I scrape the page "https://gov.wales/notifications-deaths-residents-related-covid-19-adult-care-homes"
    Then select the distribution whose title starts with "Notifications of deaths of residents related to COVID-19"
    
  Scenario: LCC dataset landing page
    Given I scrape the page "https://www.lowcarboncontracts.uk/data-portal/dataset/actual-ilr-income"
    And select the distribution given by
      | key       | value      |
      | latest    | True       |
    Then the data can be downloaded from "https://www.lowcarboncontracts.uk/data-portal/dataset/6c993439-d686-4f49-83b1-2c6e27fd17d5/resource/580a5094-ce9c-46ad-bf05-a5460a5f97b2/download/actual-ilr-income.csv"
    And the publication date should match "2021-03-18"

  Scenario: ONS scrape from seed with non supported page type
    Given I fetch the seed path "seed-ons-personal-well-being.json"
    Then building scrapper should fail with "Aborting operation This page type is not supported."

  Scenario: ONS scrape from url
    Given I scrape the page "https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/datasets/coronaviruspersonalandeconomicwellbeingimpacts"

  Scenario: ONS scrape a distribution with zero versions
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/internationaltrade/datasets/regionalisedestimatesofukserviceexports"
    And select the distribution given by
      | key       | value        |
      | latest    | True         |
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/businessindustryandtrade/internationaltrade/datasets/regionalisedestimatesofukserviceexports/2011to2016/nuts1serviceexports20112016.xls"

  Scenario: ONS scrape distributions but ignore initial versions with no stated release date
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/internationaltrade/datasets/uktradeingoodsbyclassificationofproductbyactivity"
    And select the oldest "text/csv" distribution
    Then the data can be downloaded from "https://www.ons.gov.uk/file?uri=/businessindustryandtrade/internationaltrade/datasets/uktradeingoodsbyclassificationofproductbyactivity/current/previous/v3/mq10.csv"

  Scenario: deal with ONS publication datetime as Europe/London date.
    Given I scrape the page "https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets/deathsinvolvingcovid19inthecaresectorenglandandwales"
    Then the publication date should match "2020-07-03"

  Scenario: gov.uk mediaType missing
    Given I scrape the page "https://www.gov.uk/government/statistics/alcohol-bulletin"
    Then the markdown representation should start with
    """
    ## Alcohol Bulletin

    ### Description

    Monthly statistics from the 4 different alcohol duty regimes
    """

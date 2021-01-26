Feature: Download Source data
    In an automated pipeline
    I want to download data from a scraped landing page
    
        # TODO - create a backlog item
        # Scenario: Download a standard csv as a pandas

        # TODO - create a backlog item
        # Scenario: Download an xls file as databaker

        # TODO - create a backlog item
        # Scenario: Download an xlsx file as databaker

        # TODO - create a backlog item
        # Scenario: Download an ods file as databaker

        Scenario: ApiScraper - Establish existing dataset periods on PMD4
            # Note:
            # Bit of a bodge as we don't currently have a datasets on PMD4 that's sourced
            # from an odata API via the APIScraper, so we're use a pre-existing PMD4 dataset
            # for an isolated test scenario of the period get functionality.
            Given I scrape datasets using info.json "seed-for-api-scraper-pmd4.json"
            And the dataset already exists on target PMD
            Then I identify the periods for that dataset on PMD as
            """
            http://reference.data.gov.uk/id/gregorian-interval/2020-05-04T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-04-20T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-06-08T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-03-30T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-05-18T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-03-16T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-04-06T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-04-27T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-01-13T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-03-23T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-06-15T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-02-03T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-03-02T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-03-09T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-05-11T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2019-12-30T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-01-20T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-01-06T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-06-01T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2019-12-30T00:00:00/P175D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-02-24T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-02-17T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-02-10T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-06-22T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-01-27T00:00:00/P1D, 
            http://reference.data.gov.uk/id/gregorian-interval/2020-05-25T00:00:00/P1D,
            http://reference.data.gov.uk/id/gregorian-interval/2020-04-13T00:00:00/P1D
            """

        Scenario: ApiScraper - Establish existing dataset periods on the API
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            Then I identify the periods for that dataset on the API as
            """
            http://reference.data.gov.uk/id/month/2019-01, 
            http://reference.data.gov.uk/id/month/2020-04,
            http://reference.data.gov.uk/id/month/2017-10,
            http://reference.data.gov.uk/id/month/2013-01,
            http://reference.data.gov.uk/id/month/2013-07,
            http://reference.data.gov.uk/id/month/2019-07,
            http://reference.data.gov.uk/id/month/2015-01,
            http://reference.data.gov.uk/id/month/2018-10,
            http://reference.data.gov.uk/id/month/2020-07,
            http://reference.data.gov.uk/id/month/2014-07,
            http://reference.data.gov.uk/id/month/2016-04,
            http://reference.data.gov.uk/id/month/2015-04,
            http://reference.data.gov.uk/id/month/2016-07,
            http://reference.data.gov.uk/id/month/2014-04,
            http://reference.data.gov.uk/id/month/2013-10,
            http://reference.data.gov.uk/id/month/2015-10,
            http://reference.data.gov.uk/id/month/2019-04,
            http://reference.data.gov.uk/id/month/2015-07,
            http://reference.data.gov.uk/id/month/2016-01,
            http://reference.data.gov.uk/id/month/2014-01,
            http://reference.data.gov.uk/id/month/2020-01,
            http://reference.data.gov.uk/id/month/2017-07,
            http://reference.data.gov.uk/id/month/2014-10,
            http://reference.data.gov.uk/id/month/2018-01,
            http://reference.data.gov.uk/id/month/2013-04,
            http://reference.data.gov.uk/id/month/2018-04,
            http://reference.data.gov.uk/id/month/2017-01,
            http://reference.data.gov.uk/id/month/2019-10,
            http://reference.data.gov.uk/id/month/2016-10,
            http://reference.data.gov.uk/id/month/2018-07,
            http://reference.data.gov.uk/id/month/2017-04
            """

        # download specific chunks of main dataset
        @do
        Scenario: ApiScraper - Download a period of data
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            And specify the required periods as
            """
            201901
            """
            # TODO - next line currently passing trivially
            And caching is set to "<a caching short heuristic>"
            And fetch the initial data from the API endpoint
            Then the data is equal to "odata_expected_api_data.csv"

        # download supplimentary datasets
        Scenario: ApiScraper - Download supplementary data as dictionary of 
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            And fetch the supplementary data from the API endpoint
            And caching is set to "<a caching long heuristic>"
            Then the names and dataframes returned equate to
                | keys                  | value                                 |
                | FlowType              | odata_FlowType_fixture.csv            |
                | GovRegionId           | odata_GovRegionId_fixture.csv         |
                | CountryId             | odata_CountryId_fixture.csv           |
                | CommoditySitc2Id      | odata_CommoditySitc2Id_fixture.csv    |

        # merge supplimentary data to main dataset
        Scenario: ApiScraper - Merge dataframes based on primary keys within info.json
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            And specify the required periods as
            """
            http://reference.data.gov.uk/id/month/2019-01
            """
            And fetch the initial data from the API endpoint
            And fetch the supplementary data from the API endpoint
            Then I merge the dataframes based on primary keys
            And the data is equal to "odata_api_expected_final_output.csv"
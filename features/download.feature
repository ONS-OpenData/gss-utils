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

        Scenario: ApiScraper - Establish existing dataset chunks on PMD4
            # Note:
            # Bit of a bodge as we don't currently have a datasets on PMD4 that's sourced
            # from an odata API via the APIScraper, so we're use a pre-existing PMD4 dataset
            # for an isolated test scenario of the chunk get functionality.
            Given I scrape datasets using info.json "seed-for-api-scraper-pmd4.json"
            And I select the latest distribution as the distro
            And the dataset already exists on target PMD
            Then I identify the chunks for that dataset on PMD as
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

        Scenario: ApiScraper - Establish existing dataset chunks on the API
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            And I select the latest distribution as the distro
            Then I identify the chunks for that dataset on the API as
            """
            201601, 201604, 201607, 201610, 202001, 202004, 202007, 201501, 201504, 201507, 
            201510, 201901, 201904, 201907, 201910, 201401, 201404, 201407, 201410, 201801,
            201804, 201807, 201810, 201301, 201304, 201307, 201310, 201701, 201704, 201707,
            201710
            """

        # download specific chunks of main dataset
        Scenario: ApiScraper - Download a chunk of data
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            And I select the latest distribution as the distro
            And I specify the chunk column as "MonthId"
            And I specify the required chunk as
            """
            201901
            """
            # TODO - next line currently passing trivially
            And caching is set to "<a caching short heuristic>"
            And fetch the initial data from the API endpoint
            Then the row count is "102377"
            And the column count is "7"
            And the chunk column only contains the required chunks


        # download supplimentary datasets
        Scenario: ApiScraper - Download supplementary data as dictionary
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            And I select the latest distribution as the distro
            And fetch the supplementary data from the API endpoint
            And caching is set to "<a caching long heuristic>"
            Then the names and sizes equate to
                | keys      | value   |
                | FlowType  | 4,3     |
                | Region    | 14,5    |
                | Country   | 262,15  |
                | SITC      | 3593,11 |

        # merge supplimentary data to main dataset
        Scenario: ApiScraper - Merge dataframes based on primary keys within info.json
            Given I scrape datasets using info.json "seed-for-api-scraper.json"
            And I select the latest distribution as the distro
            And I specify the required chunk as
            """
            201901
            """
            And fetch the initial data from the API endpoint
            And fetch the supplementary data from the API endpoint
            Then I merge the dataframes based on primary keys
            And the merged row count is "102377"
            And the merged column count is "39"
            And the sum of the value columns equate to
                | column   | total           |
                | Value    | 218273029127.0  |
                | NetMass  | 115815781301.0  |
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
            Given I scrape a dataset from "<some-existing-odata-dataset-url>"
            And the dataset already exists on target PMD
            Then I identify the periods for that dataset on PMD as:
            """
                <keys and values of what we've expecting... somehow>
            """

        Scenario: ApiScraper - Establish existing dataset periods on the API
            Given I scrape a dataset from "<some-existing-odata-dataset-url>"
            Then I identify the periods for that dataset on the API as:
            """
                <keys and values of what we've expecting... somehow>
            """

        Scenario: ApiScraper - Establish next period to download
            Given I scrape a dataset from "<some-existing-odata-dataset-url>"
            And the dataset already exists on target PMD
            Then the next period to download is "<period we're expecting>"

        # download specific chunks of main dataset
        Scenario: ApiScraper - Download a period of data
            Given I scrape a dataset from "<some-existing-odata-dataset-url>"
            And specify the required periods as:
            """
                <specifiy periods to represent individual chunks needing updating>
            """
            And caching is set to "<a caching short heuristic>"
            And fetch the data from the API endpoint
            Then the data is equal to "<path-to-fixture of what we're expecting>"

        # download supplimentary datasets
        Scenario: ApiScraper - Download supplementary data as dictionary of 
            Given I scrape datasets using info.json "<path-to-fixture of what we're expecting>"
            And fetch the data from the API endpoint
            And caching is set to "<a caching long heuristic>"
            Then the data is equal to "<path-to-fixture of what we're expecting>"
            # Dictionary of dataframes


        # merge supplimentary data to main dataset
        Scenario: ApiScraper - Merge dataframes based on primary keys within info.json
            Given I have scraped main dataset
            And I have scraped all supplimentary datasets
            Then I merge the dataframes based on primary keys
            And the data is equal to "<path-to-fixture of what we're expecting>"

        # note - may or may not need to represent exponential backoff here somewhere, needs a think
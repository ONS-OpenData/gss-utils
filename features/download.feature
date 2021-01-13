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

        # download whole dataset
        Scenario: ApiScraper - Download full data
            Given I scrape a dataset from "<some-existing-odata-dataset-url>"
            And fetch the data from the API endpoint
            Then the data is equal to "<path-to-fixture of what we're expecting>"

        # download specific chunks
        Scenario: ApiScraper - Download supplementary data
            Given I scrape a dataset from "<some-existing-odata-dataset-url>"
            And specify the required periods as:
            """
                <specifiy periods to represent individual chunks needing updating>
            """
            And fetch the data from the API endpoint
            Then the data is equal to "<path-to-fixture of what we're expecting>"

        # note - may or may not need to represent exponential backoff here somewhere, needs a think
Feature: Workaround issues in dependent packages
  As a developer, I need to patch some upstream issues by directly replacing functions at runtime (monkey patching).
  These fixes should be pushed upstream and once accepted, the local patches removed.

  Scenario: messytables issue with cell formatting
    Given I scrape the page "https://www.gov.uk/government/statistics/substance-misuse-treatment-for-young-people-statistics-2017-to-2018"
    And select the distribution whose title starts with "Data tables"
    And fetch the distribution as a databaker object
    Then preview the tab named "6.1.1 Trends of Age"

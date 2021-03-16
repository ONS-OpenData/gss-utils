Feature: Determine dataset themes
  In an automated pipeline
  I want to determine the dataset theme, either directly from the publisher,
  Or by manually declaring it.

  Scenario: From ONS
    Given I scrape the page "https://www.ons.gov.uk/economy/grossdomesticproductgdp/datasets/quarterlycountryandregionalgdp"
    Then dcat:theme should be `<https://www.ons.gov.uk/economy/grossdomesticproductgdp>`

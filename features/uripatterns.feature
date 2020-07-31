Feature: URI patterns
  In creating a CSV-W JSON file, we can add regular expressions to validate the values provided to URI templates.
  These regular expressions should be derivable from larger regular expressions used to represent the valid
  range of values of the URIs.

  @skip
  Scenario Outline:
    Given a URI template <template>
    And a path regular expression <regex>
    Then the <col> column can be validated against <format>

    Examples:
    | template                                    | regex            | col    | format     |
    | "http://reference.data.gov.uk/id/{+period}" | id/year/[0-9]{4} | period | ^[0-9]{4}$ |
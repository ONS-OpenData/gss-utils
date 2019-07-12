Feature: Manage CSVW metadata for transformation to RDF
  I want to derive CSVW metadata from Tidy data CSV and managed configuration data.
  I want the CSVW metadata to declare the transformation from CSV to RDF using the Data Cube Vocabulary.
  I want to include dataset definitions and dataset metadata in the CSVW metadata.

  Scenario: Create CSVW metadata for CSV2RDF to generate qb:Observations
    Given table2qb configuration at 'https://ons-opendata.github.io/ref_alcohol/'
    And a CSV file 'alohol-specific-deaths.csv'
      | Sex | Value | Period    | Underlying Cause of Death  | Measure Type | Unit   |
      | F   | 1990.0  | year/2017 | all-alcohol-related-deaths | count        | deaths |
      | F   | 0.0     | year/2017 | e24-4                      | count        | deaths |
      | F   | 177.0   | year/2017 | f10                        | count        | deaths |
      | F   | 0.0     | year/2017 | g31-2                      | count        | deaths |
      | F   | 0.0     | year/2017 | g62-1                      | count        | deaths |
    When I create a CSVW metadata file 'alcohol-specific-deaths.csv-metadata.json' for base 'http://gss-data.org.uk/data/' and path 'gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths'
    Then the metadata is valid JSON-LD
    And cloudfluff/csv2rdf generates RDF
    And the RDF should contain
    """
      @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
      @prefix qb:    <http://purl.org/linked-data/cube#> .
      @prefix sdmx-a: <http://purl.org/linked-data/sdmx/2009/attribute#> .
      @prefix sdmx-d: <http://purl.org/linked-data/sdmx/2009/dimension#> .
      @prefix sdmx-c: <http://purl.org/linked-data/sdmx/2009/code#> .
      @prefix gss-dim: <http://gss-data.org.uk/def/dimension/> .
      @prefix gss-meas: <http://gss-data.org.uk/def/measure/> .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/g31-2/count>
              a                   qb:Observation ;
              gss-dim:underlying-cause-of-death
                      <http://gss-data.org.uk/def/concept/underlying-cause-of-death/g31-2> ;
              gss-meas:count      "0.0"^^xsd:double ;
              qb:dataSet          <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
              qb:measureType      gss-meas:count ;
              sdmx-a:unitMeasure  <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
              sdmx-d:refPeriod    <http://reference.data.gov.uk/id/year/2017> ;
              sdmx-d:sex          sdmx-c:sex-F .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/all-alcohol-related-deaths/count>
              a                   qb:Observation ;
              gss-dim:underlying-cause-of-death
                      <http://gss-data.org.uk/def/concept/underlying-cause-of-death/all-alcohol-related-deaths> ;
              gss-meas:count      "1990"^^xsd:double ;
              qb:dataSet          <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
              qb:measureType      gss-meas:count ;
              sdmx-a:unitMeasure  <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
              sdmx-d:refPeriod    <http://reference.data.gov.uk/id/year/2017> ;
              sdmx-d:sex          sdmx-c:sex-F .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/f10/count>
              a                   qb:Observation ;
              gss-dim:underlying-cause-of-death
                      <http://gss-data.org.uk/def/concept/underlying-cause-of-death/f10> ;
              gss-meas:count      "177.0"^^xsd:double ;
              qb:dataSet          <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
              qb:measureType      gss-meas:count ;
              sdmx-a:unitMeasure  <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
              sdmx-d:refPeriod    <http://reference.data.gov.uk/id/year/2017> ;
              sdmx-d:sex          sdmx-c:sex-F .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/e24-4/count>
              a                   qb:Observation ;
              gss-dim:underlying-cause-of-death
                      <http://gss-data.org.uk/def/concept/underlying-cause-of-death/e24-4> ;
              gss-meas:count      "0.0"^^xsd:double ;
              qb:dataSet          <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
              qb:measureType      gss-meas:count ;
              sdmx-a:unitMeasure  <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
              sdmx-d:refPeriod    <http://reference.data.gov.uk/id/year/2017> ;
              sdmx-d:sex          sdmx-c:sex-F .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/g62-1/count>
              a                   qb:Observation ;
              gss-dim:underlying-cause-of-death
                      <http://gss-data.org.uk/def/concept/underlying-cause-of-death/g62-1> ;
              gss-meas:count      "0.0"^^xsd:double ;
              qb:dataSet          <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
              qb:measureType      gss-meas:count ;
              sdmx-a:unitMeasure  <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
              sdmx-d:refPeriod    <http://reference.data.gov.uk/id/year/2017> ;
              sdmx-d:sex          sdmx-c:sex-F .
    """

  Scenario: Create CSVW metadata for CSV2RDF with DSD
    Given table2qb configuration at 'https://ons-opendata.github.io/ref_alcohol/'
    And a CSV file 'alohol-specific-deaths.csv'
      | Sex | Value   | Period    | Underlying Cause of Death  | Measure Type | Unit   |
      | F   | 1990.0  | year/2017 | all-alcohol-related-deaths | count        | deaths |
      | F   | 0.0     | year/2017 | e24-4                      | count        | deaths |
      | F   | 177.0   | year/2017 | f10                        | count        | deaths |
      | F   | 0.0     | year/2017 | g31-2                      | count        | deaths |
      | F   | 0.0     | year/2017 | g62-1                      | count        | deaths |
    When I create a CSVW metadata file 'alcohol-specific-deaths.csv-metadata.json' for base 'http://gss-data.org.uk/data/' and path 'gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths'
    Then the metadata is valid JSON-LD
    And cloudfluff/csv2rdf generates RDF
    And the RDF should contain
    """
      @prefix qb: <http://purl.org/linked-data/cube#> .
      @prefix sdmx-a: <http://purl.org/linked-data/sdmx/2009/attribute#> .
      @prefix sdmx-d: <http://purl.org/linked-data/sdmx/2009/dimension#> .
      @prefix sdmx-c: <http://purl.org/linked-data/sdmx/2009/code#> .
      @prefix gss-dim: <http://gss-data.org.uk/def/dimension/> .
      @prefix gss-meas: <http://gss-data.org.uk/def/measure/> .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/sex>
              a             qb:ComponentSpecification ;
              qb:dimension  sdmx-d:sex .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/count>
              a           qb:ComponentSpecification ;
              qb:measure  gss-meas:count .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/underlying_cause_of_death>
              a             qb:ComponentSpecification ;
              qb:dimension  gss-dim:underlying-cause-of-death .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths>
              a             qb:DataSet ;
              qb:structure  <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/structure> .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/period>
              a             qb:ComponentSpecification ;
              qb:dimension  sdmx-d:refPeriod .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/measure_type>
              a             qb:ComponentSpecification ;
              qb:dimension  qb:measureType .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/unit>
              a             qb:ComponentSpecification ;
              qb:attribute  sdmx-a:unitMeasure .
      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/structure>
              a             qb:DataStructureDefinition ;
              qb:component  <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/unit>,
                            <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/underlying_cause_of_death>,
                            <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/sex>,
                            <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/period>,
                            <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/measure_type>,
                            <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/component/count> .
    """
    And the RDF should pass the Data Cube integrity constraints

  Scenario: Create CSVW metadata for CSV2RDF with dataset metadata
    Given I scrape the page "https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/causesofdeath/datasets/alcoholspecificdeathsintheukmaindataset"
    And set the family to 'health'
    And set the theme to <http://gss-data.org.uk/def/concept/statistics-authority-themes/health-social-care>
    And set the modified time to '2019-03-13T13:17:12'
    And table2qb configuration at 'https://ons-opendata.github.io/ref_alcohol/'
    And a CSV file 'observations.csv'
      | Age | Geography | CI Lower | Measure Type             | Sex | Unit   | CI Upper | Value | Year |
      | all | K02000001 | 0        | count                    | T   | deaths | 0        | 5701  | 2001 |
      | all | K02000001 | 10       | rate_per_100_000_persons | T   | deaths | 10       | 10    | 2001 |
    When I create a CSVW metadata file 'observations.csv-metadata.json' for base 'http://gss-data.org.uk/data/' and path 'gss_data/health/ons_alcohol_deaths_uk' with dataset metadata
    Then the metadata is valid JSON-LD
    And cloudfluff/csv2rdf generates RDF
    And the RDF should contain
    """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
      @prefix pmd: <http://publishmydata.com/def/dataset#> .
      @prefix qb: <http://purl.org/linked-data/cube#> .
      @prefix pmd: <http://publishmydata.com/def/dataset#> .
      @prefix dcat: <http://www.w3.org/ns/dcat#> .
      @prefix dct: <http://purl.org/dc/terms/> .
      @prefix gdp: <http://gss-data.org.uk/def/gdp#> .
      @prefix gov: <https://www.gov.uk/government/organisations/> .
      @prefix void: <http://rdfs.org/ns/void#> .
      <http://gss-data.org.uk/data/gss_data/health/ons_alcohol_deaths_uk> a
              qb:DataSet,
              dcat:Dataset ;
          rdfs:label "Alcohol-specific deaths in the UK"@en ;
          dct:creator gov:office-for-national-statistics ;
          dct:issued "2018-12-04"^^xsd:date ;
          dct:license <http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/> ;
          dct:modified "2019-03-13T13:17:12"^^xsd:dateTime ;
          dct:publisher gov:office-for-national-statistics ;
          dct:title "Alcohol-specific deaths in the UK"@en ;
          rdfs:comment "Annual data on age-standardised and age-specific alcohol-specific death rates in the UK, its constituent countries and regions of England."@en ;
          dcat:contactPoint <mailto:mortality@ons.gov.uk> ;
          dcat:landingPage <https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/causesofdeath/datasets/alcoholspecificdeathsintheukmaindataset> .
    """
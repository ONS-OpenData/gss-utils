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
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
          <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/all-alcohol-related-deaths/count>
          <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/all-alcohol-related-deaths> ;
          <http://gss-data.org.uk/def/measure/count> "1990"^^xsd:double;
          <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
          <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
          <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
          a <http://purl.org/linked-data/cube#Observation> .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/e24-4/count>
          <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/e24-4> ;
          <http://gss-data.org.uk/def/measure/count> "0.0"^^xsd:double ;
          <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
          <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
          <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
          a <http://purl.org/linked-data/cube#Observation> .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/f10/count>
          <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/f10> ;
          <http://gss-data.org.uk/def/measure/count> "177.0"^^xsd:double ;
          <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
          <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
          <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
          a <http://purl.org/linked-data/cube#Observation> .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/g31-2/count>
          <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/g31-2> ;
          <http://gss-data.org.uk/def/measure/count> "0.0"^^xsd:double ;
          <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
          <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
          <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
          a <http://purl.org/linked-data/cube#Observation> .

      <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/g62-1/count>
          <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/g62-1> ;
          <http://gss-data.org.uk/def/measure/count> "0.0"^^xsd:double ;
          <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
          <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
          <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
          <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
          a <http://purl.org/linked-data/cube#Observation> .
    """

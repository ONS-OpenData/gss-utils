Feature: Manage CSVW metadata for transformation to RDF
  I want to derive CSVW metadata from Tidy data CSV and managed configuration data.
  I want the CSVW metadata to declare the transformation from CSV to RDF using the Data Cube Vocabulary.
  I want to include dataset definitions and dataset metadata in the CSVW metadata.

  Scenario: Create CSVW metadata for CSV2RDF to generate qb:Observations
    Given table2qb configuration at 'https://ons-opendata.github.io/ref_health/'
    And a CSV file 'alohol-specific-deaths.csv'
      | Sex | Value | Period    | Underlying Cause of Death  | Measure Type | Unit   |
      | F   | 1990  | year/2017 | all-alcohol-related-deaths | count        | deaths |
      | F   | 0     | year/2017 | e24-4                      | count        | deaths |
      | F   | 177   | year/2017 | f10                        | count        | deaths |
      | F   | 0     | year/2017 | g31-2                      | count        | deaths |
      | F   | 0     | year/2017 | g62-1                      | count        | deaths |
      | F   | 0     | year/2017 | g72-1                      | count        | deaths |
      | F   | 19    | year/2017 | i42-6                      | count        | deaths |
      | F   | 6     | year/2017 | k29-2                      | count        | deaths |
      | F   | 1643  | year/2017 | k70                        | count        | deaths |
      | F   | 22    | year/2017 | k85-2                      | count        | deaths |
      | F   | 1     | year/2017 | k86-0                      | count        | deaths |
      | F   | 0     | year/2017 | q86-0                      | count        | deaths |
      | F   | 0     | year/2017 | r78-0                      | count        | deaths |
      | F   | 119   | year/2017 | x45                        | count        | deaths |
      | F   | 2     | year/2017 | x65                        | count        | deaths |
      | F   | 1     | year/2017 | y15                        | count        | deaths |
    When I create a CSVW metadata file 'alcohol-specific-deaths.csv-metadata.json'
    Then the metadata is valid JSON-LD
    And cloudfluff/csv2rdf generates RDF
    And the RDF should contain
    """
    <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/all-alcohol-related-deaths/count>
    <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/all-alcohol-related-deaths> ;
    <http://gss-data.org.uk/def/measure/count> 1990.0 ;
    <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
    <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
    <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
    a <http://purl.org/linked-data/cube#Observation> .

<http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/e24-4/count>
    <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/e24-4> ;
    <http://gss-data.org.uk/def/measure/count> 0.0 ;
    <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
    <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
    <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
    a <http://purl.org/linked-data/cube#Observation> .

<http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/f10/count>
    <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/f10> ;
    <http://gss-data.org.uk/def/measure/count> 177.0 ;
    <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
    <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
    <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
    a <http://purl.org/linked-data/cube#Observation> .

<http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/g31-2/count>
    <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/g31-2> ;
    <http://gss-data.org.uk/def/measure/count> 0.0 ;
    <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
    <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
    <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
    a <http://purl.org/linked-data/cube#Observation> .

<http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths/F/year/2017/g62-1/count>
    <http://gss-data.org.uk/def/dimension/underlying-cause-of-death> <http://gss-data.org.uk/def/concept/underlying-cause-of-death/g62-1> ;
    <http://gss-data.org.uk/def/measure/count> 0.0 ;
    <http://purl.org/linked-data/cube#dataSet> <http://gss-data.org.uk/data/gss_data/health/nhs-statistics-on-alcohol-england/alcohol-specific-deaths> ;
    <http://purl.org/linked-data/cube#measureType> <http://gss-data.org.uk/def/measure/count> ;
    <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://gss-data.org.uk/def/concept/measurement-units/deaths> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> <http://reference.data.gov.uk/id/year/2017> ;
    <http://purl.org/linked-data/sdmx/2009/dimension#sex> <http://purl.org/linked-data/sdmx/2009/code#sex-F> ;
    a <http://purl.org/linked-data/cube#Observation> .
    """

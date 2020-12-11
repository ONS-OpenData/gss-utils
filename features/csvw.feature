Feature: Create CSVW metadata
  I want to create CSVW metadata from a simple mapping file.
  I want the CSVW metadata to declare the transformation from CSV to RDF using the Data Cube Vocabulary.
  I want to include dataset definitions and dataset metadata in the CSVW metadata.

  Scenario: Create CSVW metadata from mapping
    Given a CSV file 'product-observations.csv'
    And a JSON map file 'mapping-info.json'
    And a dataset URI 'http://gss-data.org.uk/data/gss_data/trade/ons-uk-trade-in-goods-by-industry-country-and-commodity'
    When I create a CSVW file from the mapping and CSV
    Then the metadata is valid JSON-LD
    And gsscogs/csv2rdf generates RDF
    And the RDF should pass the Data Cube integrity constraints
    And the RDF should contain
    """
      @base <http://gss-data.org.uk/data/gss_data/trade/ons-uk-trade-in-goods-by-industry-country-and-commodity> .
      @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
      @prefix qb:    <http://purl.org/linked-data/cube#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix sdmx-a: <http://purl.org/linked-data/sdmx/2009/attribute#> .
      @prefix sdmx-d: <http://purl.org/linked-data/sdmx/2009/dimension#> .
      @prefix sdmx-c: <http://purl.org/linked-data/sdmx/2009/code#> .
      @prefix gss-dim: <http://gss-data.org.uk/def/dimension/> .
      @prefix gss-meas: <http://gss-data.org.uk/def/measure/> .
      @prefix cl_area: <http://gss-data.org.uk/def/concept-scheme/sdmx-bop/cl_area/> .

      <#dataset> a qb:DataSet ;
        qb:structure <#structure> .

      <#structure> a qb:DataStructureDefinition ;
        qb:component <#component/direction>, <#component/industry>, <#component/marker>, <#component/measure_type>,
                     <#component/commodity>, <#component/country>, <#component/value>, <#component/year>, <#component/unit> .

      <#component/direction> a qb:ComponentSpecification ;
        qb:dimension gss-dim:flow-directions .

      <#component/unit> a qb:ComponentSpecification ;
        qb:attribute sdmx-a:unitMeasure .

      <http://gss-data.org.uk/data/gss_data/trade/ons-uk-trade-in-goods-by-industry-country-and-commodity/2008/D5/46/IM/T> a qb:Observation ;
          <#dimension/commodity> <http://gss-data.org.uk/data/gss_data/trade/ons-uk-trade-in-goods-by-industry-country-and-commodity#concept/commodity/T> ;
          <#dimension/industry> <http://gss-data.org.uk/data/gss_data/trade/ons-uk-trade-in-goods-by-industry-country-and-commodity#concept/industry/46> ;
          gss-dim:flow-directions <http://gss-data.org.uk/def/concept/flow-directions/IM> ;
          gss-dim:ons-partner-geography <http://gss-data.org.uk/def/concept-scheme/sdmx-bop/cl_area/D5> ;
          sdmx-a:unitMeasure <http://gss-data.org.uk/def/concept/measurement-units/gbp> ;
          sdmx-d:refPeriod <http://reference.data.gov.uk/id/year/2008> ;
          qb:measureType gss-meas:gbp-total ;
          gss-meas:gbp-total 4.9837e+04 ;
          qb:dataSet <http://gss-data.org.uk/data/gss_data/trade/ons-uk-trade-in-goods-by-industry-country-and-commodity#dataset> ;
      .
    """

  @skip
  Scenario: Data Cube, metadata and reference data for PMD4
    Given a CSV file 'product-observations.csv'
    And a JSON map file 'mapping-info.json'
    And a dataset URI 'http://gss-data.org.uk/data/gss_data/trade/ons-uk-trade-in-goods-by-industry-country-and-commodity'
    When I create a CSVW file from the mapping and CSV
    And gsscogs/csv2rdf generates RDF
    And I add extra RDF files "cube.ttl, sdmx-dimension.ttl, trade-components.ttl, sdmx-bop.rdf, sdmx-bop-catalog.ttl, flow-directions.ttl, flow-directions-catalog.ttl"
    And I add local codelists "commodity.csv, industry.csv"
    Then the RDF should pass the PMD4 constraints

  Scenario: Local dimensions with descriptions and super properties
    Given a CSV file 'notifications.csv'
    And a JSON map file 'notifications.json'
    And a dataset URI 'http://gss-data.org.uk/data/gss_data/covid-19/wg-notifications-of-deaths-of-residents-related-to-covid-19-in-adult-care-homes'
    When I create a CSVW file from the mapping and CSV
    Then the metadata is valid JSON-LD
    And gsscogs/csv2rdf generates RDF
    And the RDF should pass the Data Cube integrity constraints
    And the RDF should contain
    """
      @base <http://gss-data.org.uk/data/gss_data/covid-19/wg-notifications-of-deaths-of-residents-related-to-covid-19-in-adult-care-homes> .
      @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
      @prefix qb:    <http://purl.org/linked-data/cube#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix sdmx-a: <http://purl.org/linked-data/sdmx/2009/attribute#> .
      @prefix sdmx-d: <http://purl.org/linked-data/sdmx/2009/dimension#> .
      @prefix sdmx-c: <http://purl.org/linked-data/sdmx/2009/code#> .
      @prefix gss-dim: <http://gss-data.org.uk/def/dimension/> .
      @prefix gss-meas: <http://gss-data.org.uk/def/measure/> .

      <#dataset> a qb:DataSet ;
        qb:structure <#structure> .

      <#structure> a qb:DataStructureDefinition ;
        qb:component <#component/notification-date>, <#component/area-code>, <#component/location-of-death>, <#component/measure_type>,
                     <#component/care-provided>, <#component/value>, <#component/unit> .

      <#component/notification-date> a qb:ComponentSpecification ;
        qb:dimension <#dimension/notification-date> .

      <#dimension/notification-date> a qb:DimensionProperty ;
        rdfs:label "Notification Date"@en ;
        rdfs:comment "Date of notification of death by the care home provider, not necessarily the date of death."@en ;
        rdfs:subPropertyOf <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> ;
        rdfs:isDefinedBy <https://gov.wales/notifications-deaths-residents-related-covid-19-adult-care-homes-1-march-14-august-2020-html#section-48615> .

      <#dimension/cause-of-death> a qb:DimensionProperty ;
        rdfs:label "Cause of Death"@en ;
        rdfs:comment "Cause of death is reported by the care home provider and not necessarily based on laboratory confirmed tests, so is not directly comparable with Public Health Wales data."@en ;
        rdfs:isDefinedBy <https://gov.wales/notifications-deaths-residents-related-covid-19-adult-care-homes-1-march-14-august-2020-html#section-48615> ;
      .

      <#component/unit> a qb:ComponentSpecification ;
        qb:attribute sdmx-a:unitMeasure .

      <#dimension/area-code> a qb:DimensionProperty ;
        rdfs:label "Area"@en ;
        qb:codeList <#scheme/area-code> ;
        rdfs:range <#class/AreaCode> ;
        rdfs:subPropertyOf <http://purl.org/linked-data/sdmx/2009/dimension#refArea> .

    """

  Scenario: CSVWMapping with compressed CSV
    Given a CSV file 'notifications.csv.gz'
    And a JSON map file 'notifications.json'
    And a dataset URI 'http://gss-data.org.uk/data/gss_data/covid-19/wg-notifications-of-deaths-of-residents-related-to-covid-19-in-adult-care-homes'
    When I create a CSVW file from the mapping and CSV
    Then the metadata is valid JSON-LD
    And the input format of the csv is recorded as csv

  Scenario: CSVMetadata from mapping with measure type and unit columns
    Given a CSV file 'observations.csv'
      | Period          | Flow    | HMRC Reporter Region | HMRC Partner Geography | SITC 4 | Value | Measure Type | Unit          |
      | quarter/2018-Q1 | exports | EA                   | A                      | 01     | 2430  | net-mass     | kg-thousands  |
      | quarter/2018-Q1 | exports | EA                   | A                      | 02     | 2     | net-mass     | kg-thousands  |
      | quarter/2018-Q4 | imports | ZB                   | TR                     | 88     | 10    | gbp-total    | gbp-thousands |
      | quarter/2018-Q4 | imports | ZB                   | TR                     | 89     | 352   | gbp-total    | gbp-thousands |
    And a column map
    """
    {
      "Period": {
        "parent": "http://purl.org/linked-data/sdmx/2009/dimension#refPeriod",
        "value": "http://reference.data.gov.uk/id/{+period}"
      },
      "Flow": {
        "dimension": "http://gss-data.org.uk/def/dimension/flow-directions",
        "value": "http://gss-data.org.uk/def/concept/flow-directions/{flow}"
      },
      "SITC 4": {
        "dimension": "http://gss-data.org.uk/def/dimension/sitc-4",
        "value": "http://gss-data.org.uk/def/concept/sitc-4/{sitc_4}"
      },
      "Value": {
        "measureRef": "Measure Type",
        "unitRef": "Unit",
        "datatype": "integer"
      }
    }
    """
    And a dataset URI 'http://gss-data.org.uk/data/gss_data/trade/hmrc_rts'
    When I create a CSVW file from the mapping and CSV
    Then the metadata is valid JSON-LD
    And gsscogs/csv2rdf generates RDF
    And the RDF should pass the Data Cube integrity constraints
    And the RDF should contain
    """
      @base <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts> .
      @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
      @prefix owl: <http://www.w3.org/2002/07/owl#> .
      @prefix void: <http://rdfs.org/ns/void#> .
      @prefix dcterms: <http://purl.org/dc/terms/> .
      @prefix dcat: <http://www.w3.org/ns/dcat#> .
      @prefix sdmx-dimension: <http://purl.org/linked-data/sdmx/2009/dimension#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#> .
      @prefix qb: <http://purl.org/linked-data/cube#> .
      @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
      @prefix sdmx-concept: <http://purl.org/linked-data/sdmx/2009/concept#> .
      @prefix gss-d: <http://gss-data.org.uk/def/dimension/> .

      <#dataset> a qb:DataSet ;
        qb:structure <#structure> .

      <#component/flow>
          qb:dimension gss-d:flow-directions ;
          a qb:ComponentSpecification .

      <#component/gbp-total>
          qb:measure <http://gss-data.org.uk/def/measure/gbp-total> ;
          a qb:ComponentSpecification .

      <#component/hmrc-partner-geography>
          qb:dimension <#dimension/hmrc-partner-geography> ;
          a qb:ComponentSpecification .

      <#component/hmrc-reporter-region>
          qb:dimension <#dimension/hmrc-reporter-region> ;
          a qb:ComponentSpecification .

      <#component/measure-type>
          qb:dimension qb:measureType ;
          a qb:ComponentSpecification .

      <#component/net-mass>
          qb:measure <http://gss-data.org.uk/def/measure/net-mass> ;
          a qb:ComponentSpecification .

      <#component/period>
          qb:dimension sdmx-dimension:refPeriod ;
          a qb:ComponentSpecification .

      <#component/sitc4>
          qb:dimension gss-d:sitc-4 ;
          a qb:ComponentSpecification .

      <#component/unit>
          qb:attribute sdmx-attribute:unitMeasure ;
          a qb:ComponentSpecification .

      <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts/quarter/2018-Q1/exports/EA/A/01/net-mass>
          gss-d:flow-directions <http://gss-data.org.uk/def/concept/flow-directions/exports> ;
          gss-d:sitc-4 <http://gss-data.org.uk/def/concept/sitc-4/01> ;
          gss-d:hmrc-partner-geography <http://gss-data.org.uk/def/concept/hmrc-geographies/A> ;
          gss-d:hmrc-reporter-region <http://gss-data.org.uk/def/concept/hmrc-regions/EA> ;
          <http://gss-data.org.uk/def/measure/net-mass> 2.43E3 ;
          qb:dataSet <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts> ;
          qb:measureType <http://gss-data.org.uk/def/measure/net-mass> ;
          sdmx-attribute:unitMeasure <http://gss-data.org.uk/def/concept/measurement-units/kg-thousands> ;
          sdmx-dimension:refPeriod <http://reference.data.gov.uk/id/quarter/2018-Q1> ;
          a qb:Observation .

      <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts/quarter/2018-Q1/exports/EA/A/02/net-mass>
          gss-d:flow-directions <http://gss-data.org.uk/def/concept/flow-directions/exports> ;
          gss-d:sitc-4 <http://gss-data.org.uk/def/concept/sitc-4/02> ;
          gss-d:hmrc-partner-geography <http://gss-data.org.uk/def/concept/hmrc-geographies/A> ;
          gss-d:hmrc-reporter-region <http://gss-data.org.uk/def/concept/hmrc-regions/EA> ;
          <http://gss-data.org.uk/def/measure/net-mass> 2.0E0 ;
          qb:dataSet <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts> ;
          qb:measureType <http://gss-data.org.uk/def/measure/net-mass> ;
          sdmx-attribute:unitMeasure <http://gss-data.org.uk/def/concept/measurement-units/kg-thousands> ;
          sdmx-dimension:refPeriod <http://reference.data.gov.uk/id/quarter/2018-Q1> ;
          a qb:Observation .

      <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts/quarter/2018-Q4/imports/ZB/TR/88/gbp-total>
          gss-d:flow-directions <http://gss-data.org.uk/def/concept/flow-directions/imports> ;
          gss-d:sitc-4 <http://gss-data.org.uk/def/concept/sitc-4/88> ;
          gss-d:hmrc-partner-geography <http://gss-data.org.uk/def/concept/hmrc-geographies/TR> ;
          gss-d:hmrc-reporter-region <http://gss-data.org.uk/def/concept/hmrc-regions/ZB> ;
          <http://gss-data.org.uk/def/measure/gbp-total> 1.0E1 ;
          qb:dataSet <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts> ;
          qb:measureType <http://gss-data.org.uk/def/measure/gbp-total> ;
          sdmx-attribute:unitMeasure <http://gss-data.org.uk/def/concept/measurement-units/gbp-thousands> ;
          sdmx-dimension:refPeriod <http://reference.data.gov.uk/id/quarter/2018-Q4> ;
          a qb:Observation .

      <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts/quarter/2018-Q4/imports/ZB/TR/89/gbp-total>
          gss-d:flow-directions <http://gss-data.org.uk/def/concept/flow-directions/imports> ;
          gss-d:sitc-4 <http://gss-data.org.uk/def/concept/sitc-4/89> ;
          gss-d:hmrc-partner-geography <http://gss-data.org.uk/def/concept/hmrc-geographies/TR> ;
          gss-d:hmrc-reporter-region <http://gss-data.org.uk/def/concept/hmrc-regions/ZB> ;
          <http://gss-data.org.uk/def/measure/gbp-total> 3.52E2 ;
          qb:dataSet <http://gss-data.org.uk/data/gss_data/trade/hmrc_rts> ;
          qb:measureType <http://gss-data.org.uk/def/measure/gbp-total> ;
          sdmx-attribute:unitMeasure <http://gss-data.org.uk/def/concept/measurement-units/gbp-thousands> ;
          sdmx-dimension:refPeriod <http://reference.data.gov.uk/id/quarter/2018-Q4> ;
          a qb:Observation .

      <#structure>
          qb:component <#component/flow>,
                       <#component/gbp_total>,
                       <#component/hmrc_partner_geography>,
                       <#component/hmrc_reporter_region>,
                       <#component/measure_type>,
                       <#component/net_mass>,
                       <#component/period>,
                       <#component/sitc4>,
                       <#component/unit> ;
          a qb:DataStructureDefinition .
    """
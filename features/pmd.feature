Feature: PMD metadata
  In an automated pipeline
  I want to build an RDF graph out of dataset metadata and ensure
  PMD specific terms are used.

  Scenario: generate metadata
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    And set the base URI to <http://gss-data.org.uk>
    And set the dataset ID to <foreign-direct-investment-inward>
    And set the theme to <business-industry-trade-energy>
    And set the family to 'trade'
    And set the license to 'OGLv3'
    And set the modified time to '2018-09-14T10:04:33.141484+01:00'
    And set the description to 'Inward Foreign Direct Investment (FDI) Involving UK Companies, 2016 (Directional Principle)'
    And generate TriG
    Then the TriG should contain
      """
      @prefix dct: <http://purl.org/dc/terms/> .
      @prefix dcat: <http://www.w3.org/ns/dcat#> .
      @prefix gdp: <http://gss-data.org.uk/def/gdp#> .
      @prefix ns1: <http://gss-data.org.uk/graph/foreign-direct-investment-inward/> .
      @prefix pmdcat: <http://publishmydata.com/pmdcat#> .
      @prefix qb: <http://purl.org/linked-data/cube#> .
      @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix void: <http://rdfs.org/ns/void#> .
      @prefix xml: <http://www.w3.org/XML/1998/namespace> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <http://gss-data.org.uk/graph/foreign-direct-investment-inward/metadata> {
        <http://gss-data.org.uk/data/foreign-direct-investment-inward-catalog-entry> a pmdcat:Dataset ;
        rdfs:label "Foreign direct investment involving UK companies: inward"@en ;
        dcat:theme <http://gss-data.org.uk/def/concept/statistics-authority-themes/business-industry-trade-energy>;
        gdp:family gdp:trade ;
        dcat:contactPoint <mailto:fdi@ons.gov.uk> ;
        pmdcat:graph <http://gss-data.org.uk/graph/foreign-direct-investment-inward> ;
        pmdcat:datasetContents <http://gss-data.org.uk/data/foreign-direct-investment-inward> ;
        dct:creator <https://www.gov.uk/government/organisations/office-for-national-statistics> ;
        dct:issued "2019-12-03"^^xsd:date ;
        dct:license <http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/> ;
        dct:publisher <https://www.gov.uk/government/organisations/office-for-national-statistics> ;
        dct:title "Foreign direct investment involving UK companies: inward"@en ;
        void:sparqlEndpoint <http://gss-data.org.uk/sparql> ;
        rdfs:comment "Annual statistics on the investment of foreign companies into the UK, including for investment flows, positions and earnings."@en ;
        dct:description "Inward Foreign Direct Investment (FDI) Involving UK Companies, 2016 (Directional Principle)"@en .
      }
      """

    Scenario: convention over configuration
      Given the 'JOB_NAME' environment variable is 'GSS_data/Trade/ONS-FDI-inward'
      And I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
      And generate TriG
      Then the dataset contents URI should be <http://gss-data.org.uk/data/gss_data/trade/ons-fdi-inward>
      And the metadata graph should be <http://gss-data.org.uk/graph/gss_data/trade/ons-fdi-inward>
      And the modified date should be quite recent

    Scenario: licensed dataset
      Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
      Then dct:license should be `<http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>`

    Scenario: modified or updated
      Given I scrape the page "https://www.gov.uk/government/statistics/immigration-statistics-october-to-december-2017-data-tables"
      Then the modified date should be quite recent

    Scenario: catalog scraped datasets
      Given the 'JOB_NAME' environment variable is 'GSS_data/Health/ISD-Drugs-and-Alcohol'
      Given I scrape the page "http://www.isdscotland.org/Health-Topics/Drugs-and-Alcohol-Misuse/Publications/"
      And I select the dataset "National Drug and Alcohol Treatment Waiting Times"
      Then generate TriG

    Scenario: generate catalogue metadata for PMD4
      Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompaniesoutwardtables"
      And set the base URI to <http://gss-data.org.uk>
      And set the dataset ID to <gss_data/trade/ons-fdi>
      And set the family to 'trade'
      And set the theme to <business-industry-trade-energy>
      And generate TriG
      Then the TriG should contain triples given by "pmd4-metadata.ttl"
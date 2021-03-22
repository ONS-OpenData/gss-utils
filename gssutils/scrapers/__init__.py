from gssutils.scrapers import ons, onscmd, govuk, nrscotland, nisra, hmrc, ni_govuk, isd_scotland, nhs_digital, statswales,\
    govscot, dcni, govwales, lcc

scraper_list = [
    ('https://api.beta.ons.gov.uk', onscmd.scrape),
    ('https://www.ons.gov.uk/', ons.scrape),
    ('https://www.gov.uk/government/', govuk.content_api),
    ('https://www.ethnicity-facts-figures.service.gov.uk/', govuk.eth_facts_service),
    ('https://www.nrscotland.gov.uk/statistics-and-data/statistics/', nrscotland.statistics_handler),
    ('https://www.nrscotland.gov.uk/covid19stats', nrscotland.covid_handler),
    ('https://www.nisra.gov.uk/publications/', nisra.scrape),
    ('https://www.uktradeinfo.com/Statistics/Pages/', hmrc.scrape_pages),
    ('https://www.uktradeinfo.com/Statistics/OverseasTradeStatistics/AboutOverseastradeStatistics/Pages/OTSReports.aspx',
     hmrc.scrape_ots_reports),
    ('https://www.uktradeinfo.com/Statistics/RTS/Pages/default.aspx', hmrc.scrape_rts),
    ('https://www.justice-ni.gov.uk/publications/', ni_govuk.scrape),
    ('https://www.health-ni.gov.uk/publications/', ni_govuk.scrape),
    ('http://www.isdscotland.org/Health-Topics/', isd_scotland.scrape),
    ('https://digital.nhs.uk/data-and-information/publications/statistical/', nhs_digital.scrape),
    ('https://statswales.gov.wales/Catalogue', statswales.scrape),
    ('https://www.gov.scot', govscot.scrape),
    ('https://www2.gov.scot/Topics/Statistics/Browse/', govscot.scrape),
    ('https://www.communities-ni.gov.uk/publications/topic', dcni.scrape),
    ('https://www.communities-ni.gov.uk/topic', dcni.scrape),
    ('https://gov.wales/', govwales.scrape),
    ('https://www.lowcarboncontracts.uk/data-portal/dataset', lcc.scrape),
    ('https://www.gov.uk/guidance', govuk.guidance_scraper)
]

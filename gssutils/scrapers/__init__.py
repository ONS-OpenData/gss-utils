from gssutils.scrapers import ons, govuk, nrscotland, nisra, hmrc, ni_govuk, isd_scotland

scraper_list = [
    ('https://www.ons.gov.uk/', ons.scrape),
    ('https://www.gov.uk/government/statistics/', govuk.scrape_stats),
    ('https://www.gov.uk/government/statistical-data-sets/', govuk.scrape_sds),
    ('https://www.nrscotland.gov.uk/statistics-and-data/statistics/', nrscotland.scrape),
    ('https://www.nisra.gov.uk/publications/', nisra.scrape),
    ('https://www.uktradeinfo.com/Statistics/Pages/', hmrc.scrape),
    ('https://www.justice-ni.gov.uk/publications/', ni_govuk.scrape),
    ('https://www.health-ni.gov.uk/publications/', ni_govuk.scrape),
    ('http://www.isdscotland.org/Health-Topics/', isd_scotland.scrape)
]
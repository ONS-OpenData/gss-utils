from gssutils.scrapers import ons, govuk, nrscotland, nisra, hmrc

scraper_list = [
    ('https://www.ons.gov.uk/', ons.scrape),
    ('https://www.gov.uk/government/statistics/', govuk.scrape_stats),
    ('https://www.gov.uk/government/statistical-data-sets/', govuk.scrape_sds),
    ('https://www.nrscotland.gov.uk/statistics-and-data/statistics/', nrscotland.scrape),
    ('https://www.nisra.gov.uk/publications/', nisra.scrape),
    ('https://www.uktradeinfo.com/Statistics/Pages/', hmrc.scrape)
]
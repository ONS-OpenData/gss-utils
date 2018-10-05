from gssutils.scrapers import ons, govuk, nrscotland

scraper_list = [
    ('https://www.ons.gov.uk/', ons.scrape),
    ('https://www.gov.uk/government/statistics/', govuk.scrape),
    ('https://www.nrscotland.gov.uk/statistics-and-data/statistics/', nrscotland.scrape)
]
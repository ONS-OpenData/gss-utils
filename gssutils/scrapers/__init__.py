from gssutils.scrapers import ons, govuk, nrscotland, nisra

scraper_list = [
    ('https://www.ons.gov.uk/', ons.scrape),
    ('https://www.gov.uk/government/statistics/', govuk.scrape),
    ('https://www.nrscotland.gov.uk/statistics-and-data/statistics/', nrscotland.scrape),
    ('https://www.nisra.gov.uk/publications/', nisra.scrape)
]
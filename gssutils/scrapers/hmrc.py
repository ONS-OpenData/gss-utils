from urllib.parse import urljoin
from gssutils.metadata import Dataset, Excel, Distribution, PMDDataset, GOV
from dateutil.parser import parse


def scrape(scraper, tree):
    scraper.catalog.title = tree.xpath("//title/text()")[0].strip()
    scraper.catalog.dataset = []
    scraper.catalog.set_uri(scraper.uri + "#catalog")
    scraper.catalog.publisher = GOV['hm-revenue-customs']
    scraper.catalog.rights = "https://www.uktradeinfo.com/AboutUs/Pages/TermsAndConditions.aspx"
    # from above terms, link to crown copyright at the National Archives says default license is OGL
    scraper.catalog.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    # just scrape the first table for now; others are archives or factsheets.
    table = tree.xpath("//table[contains(concat(' ', @class, ' '), ' hmrc ')]")[0]
    header = True
    columns = []
    for row in table.xpath("tbody/tr"):
        if header:
            columns = [t.strip() for t in row.xpath("th/text()")]
            header = False
        else:
            dataset = PMDDataset()
            dataset.publisher = scraper.catalog.publisher
            dataset.license = scraper.catalog.license
            bulletin_date = None
            for k, v in zip(columns, row.xpath("td")):
                if k == 'Bulletin Title':
                    dataset.title = v.text
                elif k == 'Publication Source':
                    pass
                elif k == 'Release Date':
                    dataset.issued = parse(v.text.strip())
                elif k == 'Bulletin Date':
                    bulletin_date = v.text
                elif k == 'View Bulletin':
                    href = v.xpath("a/@href")[0]
                    dist = Distribution(scraper)
                    dist.downloadURL = urljoin(scraper.uri, href)
                    if dist.downloadURL.endswith('.xls') or dist.downloadURL.endswith('.xlsx'):
                        dist.mediaType = Excel
                    dist.title = dataset.title + (' ' + bulletin_date) if bulletin_date else ''
                    dataset.distribution = [dist]
            scraper.catalog.dataset.append(dataset)

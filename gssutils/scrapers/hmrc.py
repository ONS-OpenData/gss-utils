from urllib.parse import urljoin
from gssutils.metadata import Dataset, Excel, Distribution
from dateutil.parser import parse

def scrape(scraper, tree):
    scraper.catalog.title = tree.xpath("//title/text()")[0].strip()
    for table in tree.xpath("//table[contains(concat(' ', @class, ' '), ' hmrc ')]"):
        header = True
        columns = []
        for row in table.xpath("tbody/tr"):
            if header:
                columns = [t.strip() for t in row.xpath("th/text()")]
                header = False
            else:
                dataset = Dataset()
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
                        scraper.distributions.append(dist)
                scraper.datasets.append(dataset)
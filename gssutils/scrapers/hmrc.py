import logging
import mimetypes
from urllib.parse import urljoin
from gssutils.metadata import Dataset, Excel, Distribution, PMDDataset, GOV
from dateutil.parser import parse


def scrape_pages(scraper, tree):
    scraper.catalog.title = tree.xpath("//title/text()")[0].strip()
    scraper.catalog.dataset = []
    scraper.catalog.uri = scraper.uri + "#catalog"
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


def scrape_ots_reports(scraper, tree):
    scraper.catalog.title = tree.xpath("//title/text()")[0].strip()
    scraper.catalog.dataset = []
    scraper.catalog.uri = scraper.uri + "#catalog"
    scraper.catalog.publisher = GOV['hm-revenue-customs']
    scraper.catalog.rights = "https://www.uktradeinfo.com/AboutUs/Pages/TermsAndConditions.aspx"
    # from above terms, link to crown copyright at the National Archives says default license is OGL
    scraper.catalog.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    dataset_titles = {}
    table = tree.xpath("//h1/following-sibling::table")[0]
    header = True
    columns = []
    for row in table.xpath("tbody/tr"):
        if header:
            columns = [t.strip() for t in row.xpath("th/text()")]
            header = False
        else:
            publication_date = None
            for k, v in zip(columns, row.xpath("td")):
                if k == 'Published':
                    try:
                        if v.text is not None:
                            publication_date = parse(v.text.strip().strip(u'\u200B\ufeff'))
                    except ValueError as e:
                        logging.warning(f"Unable to parse published date {e}")
                elif k == 'Report':
                    links = v.xpath('a')
                    if len(links) > 0:
                        if links[0].get('href').startswith('https://www.gov.uk/government/statistics/'):
                            logging.warning(f'Dataset is published at gov.uk, see {links[0].get("href")}')
                            continue
                        title = links[0].text.strip().strip(u'\u200B\ufeff')
                        if title not in dataset_titles:
                            dataset = PMDDataset()
                            if publication_date is not None:
                                dataset.issued = publication_date
                            dataset.publisher = scraper.catalog.publisher
                            dataset.license = scraper.catalog.license
                            dataset.title = links[0].text.strip().strip(u'\u200B\ufeff')
                            dataset.distribution = []
                            dataset_titles[title] = dataset
                        else:
                            dataset = dataset_titles[title]
                            if publication_date is not None and publication_date > dataset.issued:
                                dataset.issued = publication_date
                        for dist_link in links:
                            dist = Distribution(scraper)
                            dist.title = dist_link.text.strip().strip(u'\u200B\ufeff')
                            dist.downloadURL = urljoin(scraper.uri, dist_link.get('href'))
                            dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
                            dataset.distribution.append(dist)
    if len(dataset_titles) > 0:
        scraper.catalog.dataset = list(dataset_titles.values())


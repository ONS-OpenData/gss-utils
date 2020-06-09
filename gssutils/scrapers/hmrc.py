import logging
import mimetypes
from urllib.parse import urljoin

from dateutil.parser import parse
from lxml import html

from gssutils.metadata import GOV, THEME
from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import Excel
from gssutils.metadata.pmdcat import Dataset


def scrape_pages(scraper, tree):
    scraper.catalog.title = tree.xpath("//title/text()")[0].strip()
    scraper.catalog.dataset = []
    scraper.catalog.uri = scraper.uri + "#catalog"
    scraper.catalog.publisher = GOV['hm-revenue-customs']
    scraper.catalog.rights = "https://www.uktradeinfo.com/AboutUs/Pages/TermsAndConditions.aspx"
    # from above terms, link to crown copyright at the National Archives says default license is OGL
    scraper.catalog.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    # just scrape the first table for now; others are archives or factsheets.
    tables = tree.xpath("//table[contains(concat(' ', @class, ' '), ' hmrc ') or (contains(@summary, 'Tax & Duty bulletins'))]")
    for table in tables:
        header = True
        columns = []
        for row in table.xpath("tbody/tr"):
            if header:
                columns = [t.strip() for t in row.xpath("th/text()")]
                header = False
            else:
                dataset = Dataset(scraper.uri)
                dataset.publisher = scraper.catalog.publisher
                dataset.license = scraper.catalog.license
                dataset.distribution = []
                bulletin_date = None
                for k, v in zip(columns, row.xpath("td")):
                    if k == 'Bulletin Title' or k == 'Title' or k == 'Factsheet Title':
                        dataset.title = v.text
                    elif k == 'Publication Source' or k == 'Source':
                        pass
                    elif k == 'Release Date' or k == 'Released':
                        dataset.issued = parse(v.text.strip())
                    elif k == 'Bulletin Date' or k == 'Period':
                        bulletin_date = v.text
                    elif k == 'View' or k == 'View Archive':
                        href = v.xpath("a/@href")[0]
                        view_url = urljoin(scraper.uri, href)
                        if '?viewname' in view_url:
                            # this is a link off to a separate "archive" page with links to the
                            # actual dataset releases
                            archive_page = scraper.session.get(view_url)
                            archive_tree = html.fromstring(archive_page.text)
                            for release_row in archive_tree.xpath("//table[@class='hmrc']//tr")[1:]:
                                dist = Distribution(scraper)
                                cols = release_row.xpath("td")
                                dist.downloadURL = urljoin(view_url, cols[1].xpath("a/@href")[0].replace(' ', '%20'))
                                archive_date = cols[0].text
                                dist.issued = parse(archive_date.strip())
                                dist.mediaType, _ = mimetypes.guess_type(dist.downloadURL)
                                dist.title = dataset.title + ' ' + archive_date
                                dataset.distribution.append(dist)
                        else:
                            dist = Distribution(scraper)
                            dist.downloadURL = urljoin(scraper.uri, href)
                            if dist.downloadURL.endswith('.xls') or dist.downloadURL.endswith('.xlsx'):
                                dist.mediaType = Excel
                            dist.title = dataset.title + (' ' + bulletin_date) if bulletin_date else ''
                            dataset.distribution.append(dist)
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
                            dataset = Dataset(scraper.uri)
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


def scrape_rts(scraper, metadata_tree):
    """
        HMRC RTS is a special case, where the main page is:
          https://www.uktradeinfo.com/Statistics/RTS/Pages/default.aspx
        the RTS dataset metadata is available from:
          https://www.uktradeinfo.com/Lists/HMRC%20%20Metadata/DispForm.aspx?ID=3&ContentTypeId=0x0100E95984F4DBD401488EB2E5697A7B38EF
        and the zipped data files are linked from:
          https://www.uktradeinfo.com/Statistics/RTS/Pages/RTS-Downloads.aspx
    """
    METADATA_URL = 'https://www.uktradeinfo.com/Lists/HMRC%20%20Metadata/DispForm.aspx?ID=3&ContentTypeId=0x0100E95984F4DBD401488EB2E5697A7B38EF'
    DISTRIBUTION_URL = 'https://www.uktradeinfo.com/Statistics/RTS/Pages/RTS-Downloads.aspx'
    # from above terms, link to crown copyright at the National Archives says default license is OGL
    scraper.dataset.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    # Ideally, as this looks like a Snarepoint site, we should be able to fetch the metadata as JSON via tha Snarepoint
    # "REST" (where MS still wrongly say REST means CRUD) interface. But we can't, so let's just scrape.
    metadata_page = scraper.session.get(METADATA_URL)
    metadata_tree = html.fromstring(metadata_page.text)

    def metadata_value(prop):
        return ' '.join(metadata_tree.xpath(f"//tr[td/h3/text() = '{prop}']/td[2]/text()")).strip()

    scraper.dataset.title = metadata_value('Title')
    scraper.dataset.description = metadata_value('Identification:Abstract')
    assert metadata_value('Organisation:Responsible Organisation') == 'HM Revenue & Customs – Trade Statistics.', \
        "Expecting org to be 'HM Revenue & Customs – Trade Statistics.', got '" + \
        metadata_value('Organisation:Responsible Organisation') + "'."
    scraper.dataset.publisher = GOV['hm-revenue-customs']
    scraper.dataset.rights = "https://www.uktradeinfo.com/AboutUs/Pages/TermsAndConditions.aspx"
    scraper.dataset.contactPoint = metadata_tree.xpath("//tr[td/h3/text() = 'Organisation:Email Address']/td[2]/a/@href")[0]
    scraper.dataset.keyword = [
        keyword.strip().rstrip('.') for keyword in metadata_value('Classification:Keyword').split(',')]
    assert metadata_value('Classification:National Statistics Theme') == 'Business and Energy', \
        "Expecting National Statistics Theme to be 'Business and Energy"
    assert metadata_value('Classification:Sub-theme') == 'International Trade', \
        "Expecting sub-theme to be 'International Trade"
    scraper.dataset.theme = THEME['business-industry-trade-energy']

    # now fetch list of distributions
    distributions_page = scraper.session.get(DISTRIBUTION_URL)
    distributions_tree = html.fromstring(distributions_page.text)
    for anchor in distributions_tree.xpath("//div[h1[text()='closed periods']]/ul/li/a"):
        dist = Distribution(scraper)
        dist.title = anchor.text.strip()
        dist.downloadURL = urljoin(scraper.uri, anchor.get('href'))
        dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
        scraper.distributions.append(dist)
        
    for anchor in distributions_tree.xpath("//div[h1[text()='Open periods']]/ul/li/a"):
        dist2 = Distribution(scraper)
        dist2.title = anchor.text.strip()
        dist2.downloadURL = urljoin(scraper.uri, anchor.get('href'))
        dist2.mediaType, encoding = mimetypes.guess_type(dist2.downloadURL)
        scraper.distributions.append(dist2)


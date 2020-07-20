from dateutil.parser import parse
from lxml import html

from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import ODS, Excel
import gssutils.scrapers


def scrape(scraper, tree):

    # A quick safety in case people are using this scraper incorrectly
    if "?search=" not in scraper.uri:
        raise Exception("""Aborting. This scraper is intended to run off the DCNI seach page.
        Please modify your url to use the site search.

        If in doubt, work from this page, change the quoted search text and capture the url
        https://www.communities-ni.gov.uk/publications/topic/8182?search=%22Northern+Ireland+Housing+Bulletin%22&Search-exposed-form=Go&sort_by=field_published_date
        """)

    scraper.dataset.publisher = GOV['department-for-communities-northern-ireland']
    scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-" \
        "government-licence/version/3/'

    # We're taking each search result as a distribution
    search_result_urls = []
    for linkObj in tree.xpath("//h3/a"):

        # linkObj.items() is eg ("href", "www.foo.com") where we want a url
        href = [x[1] for x in linkObj.items() if x[0] == "href"][0]

        # Add to distributions url list, get the root from the original url
        search_result_urls.append(scraper.uri.split("/publications/topic")[0] + href)

    # keep track of dates issued so we can find the latest
    last_issued = None

    for url in search_result_urls:

        # Get the distribution page
        page = scraper.session.get(url)
        distro_tree = html.fromstring(page.text)

        # Get any spreadsheets (ods or excel) linked on the page
        spreadsheet_files = [x for x in distro_tree.xpath('//a/@href') if x.lower().endswith(".ods") or x.lower().endswith(".xlsx")]

        # Now map them together, so we have the supporting info for each relevent download
        # TODO - make better, kinda nasty
        title_download_map = {}
        for spreadsheet_file in spreadsheet_files:

            # Create our new distribution object
            this_distribution = Distribution(scraper)

            # Identify the correct title
            this_distribution.title = distro_tree.xpath("//a[@href='" + spreadsheet_file + "']/text()".format(spreadsheet_file))[0]
            this_distribution.downloadURL = spreadsheet_file

            if this_distribution.downloadURL.lower().endswith(".xlsx"):
                media_type = Excel
            elif this_distribution.downloadURL.lower().endswith(".ods"):
                media_type = ODS
            else:
                raise Exception("Aborting. Unexpected media type for url: '{}'"
                                .format(this_distribution.downloadURL))
            this_distribution.mediaType = media_type

            # Published and modifed time
            this_distribution.issued = parse(distro_tree.xpath("//*[@property='article:published_time']/@content")[0],
                                             parserinfo=gssutils.scrapers.UK_DATES).date()
            this_distribution.modified = parse(distro_tree.xpath("//*[@property='article:modified_time']/@content")[0],
                                               parserinfo=gssutils.scrapers.UK_DATES).date()
            this_distribution.description = distro_tree.xpath("//*[@class='field-summary']/p/text()")[0]

            if last_issued is None:
                last_issued = this_distribution.issued
            elif this_distribution.issued > last_issued:
                last_issued = this_distribution.issued

            scraper.distributions.append(this_distribution)

    # Whatever date the latest distribution was issued, is the last issued date for this "dataset"
    scraper.dataset.issued = last_issued

import logging
import mimetypes
import re
from urllib.parse import urljoin

from dateutil.parser import parse

from gssutils.metadata import Distribution, Excel, ODS, CSV, CSDB

import requests

import json

ONS_PREFIX = "http://www.ons.gov.uk"
ONS_DOWNLOAD_PREFIX = ONS_PREFIX+"/file?uri="


def scrape(scraper, tree):
    """
    This top level scrap-class uses the initial "tree" provided to choose  between using a
    page-type specific json scraper or using the pre-existing html scraper.

    If the pge is json-able you'll get the handler for the page type you've provided,
    or you'll get a exception telling you we don't handle it (yet...).

    If it's not json-able, we'll call the older scraper with a depreciation warning.

    :param scraper:     The Scraper Object
    :param tree:        an lxml etree of the initial scrape
    :return:
    """

    # If we can't load it as json we'll have to have to assume it's coming from an older recipe,
    # so we'll throw a depreciation warning and use the old scraper.
    try:
        p = tree.xpath("//p/text()")[0].strip()
        initial_page = json.loads(p)
    except:
        logging.warning("This is not json-able content. Attempting to parse with depreciated html scraper.")
        depreciated_scraper(scraper, tree)
        return

    # handers, one per page_type, add to this as needed
    page_handlers = {
        "dataset_landing_page": onshandler_dataset_landing_page
    }

    # throw an exception if it's a json page type we don't handle
    page_type = initial_page["type"]
    if page_type not in page_handlers:
        raise ValueError("Aborting. The ONS scraper does not handle ./data pages of type: " + page_type)

    logging.debug("Calling handler for page type: " + page_type)

    handler = page_handlers[page_type]
    handler(scraper, initial_page)


def onshandler_dataset_landing_page(scraper, landing_page):
    """
    This is the handler for the page type of "dataset_landing_page"

    The intention is to get the basic metadata from this page, then look at the provided
    /current link (and its "previous version" info) and create a .distribution for each
    format type of each previous version of said dataset.

    :param scraper:         the Scraper object
    :param landing_page:    the json representation of a dataset_landing_page
    :return:
    """

    # sanity check, make sure the page really is just dealing with one dataset
    if len(landing_page["datasets"]) != 1:
        raise ValueError("Aborting. More than one dataset linked on a dataset landing page: {}." \
                         .format(",".join(landing_page["datasets"])))

    # Acquire basic metadata from the dataset_landing_page
    scraper.dataset.title = landing_page["description"]["title"]
    scraper.dataset.description = landing_page["description"]["metaDescription"]
    scraper.dataset.issued = parse(landing_page["description"]["releaseDate"])
    scraper.dataset.updateDueOn = parse(landing_page["description"]["nextRelease"])

    # get contact info now, as it's only available via json at the landing_page level
    # note, adding mailto: prefix so the property gets correctly identified by metadata.py
    contact_dict = landing_page["description"]["contact"]
    scraper.dataset.contactPoint = "mailto:"+contact_dict["email"]

    # Get json "scrape" of the ./current page
    page_url = ONS_PREFIX+landing_page["datasets"][0]["uri"]+"/data"
    r = requests.get(page_url)
    if r.status_code != 200:
        raise ValueError("Scrape of url '{}' failed with status code {}." \
                         .format(page_url, r.status_code))

    current_dataset_page = r.json() # dict-ify

    # start a dictionary of dataset versions (to hold current + all previous) as
    # {url: release_date}, start with just the current/latest version
    versions_dict = {ONS_PREFIX + landing_page["datasets"][0]["uri"]+"/data":
                                    landing_page["description"]["releaseDate"]}

    # then add all the older version to that dictionary
    for version_as_dict in current_dataset_page["versions"]:
        versions_dict.update({ONS_PREFIX+version_as_dict["uri"]+"/data":
                                    version_as_dict["updateDate"]})

    # iterate through the lot, creating a distribution objects for each
    # then add it to the list scraper.distributions[]
    for distro_url, release_date in versions_dict.items():
        logging.debug("Identified distribution url, building distribution object for: " + distro_url)

        r = requests.get(distro_url)
        if r.status_code != 200:
            raise ValueError("Aborting. Scraper unable to acquire the page: "+ distro_url)

        this_page = r.json()    # dict-ify

        # Get the download urls, if there's more than 1,each forms a separate distribution
        distribution_formats = this_page["downloads"]
        for dl in distribution_formats:

            # Distribution object to represent this distribution
            this_distribution = Distribution(scraper)
            this_distribution.issued = parse(release_date)

            assert 'file' in dl.keys(), "Aborting, expecting dict with 'file' key. Instead " \
                    + "we got: {}.".format(str(dl))


            download_url = ONS_DOWNLOAD_PREFIX+this_page["uri"]+"/"+dl["file"]
            this_distribution.downloadURL = download_url
            this_distribution.mediaType = download_url.split('.')[1]

            # Get file size
            """
            # TODO - better, this is a bit nasty.

            It's because my old pal zebedee (ONS content file server) is resisting all
            attempts to give out file information beyond letting you download the file.

            Am having to switch back to the html page and nip out the hard coded file size.
            """

            lines_in_html_page = [x for x in requests.get(distro_url[:-5]).text.split("\n")]

            file_extension_sought = download_url.split(".")[-1]
            file_size_text = None

            for i in range(0, len(lines_in_html_page)):
                if "MB)" in lines_in_html_page[i]:
                    previous_line = lines_in_html_page[i-1]

                    # the text for csv or xlsx should match the file type
                    if previous_line.strip() == file_extension_sought:
                        file_size_text = lines_in_html_page[i]

                    # otherwise specifically check it its csdb
                    elif previous_line.strip() == "text" and file_extension_sought == "csdb":
                        file_size_text = lines_in_html_page[i]

            assert file_size_text != None, "Unable to find file size for '{}' from '{}'." \
                    .format(download_url, distro_url[:-5])

            # We'll use a wordy try catch as this is the bit most likely to blow up
            should_be_floatable = file_size_text[1:].split(" ")[0]
            try:
                this_distribution.byteSize = float(should_be_floatable) * 1000
            except ValueError as ve:
                raise ValueError("Issue encountered attempting to turn '{}' from '{}' into float. "
                            "Source page was '{}', for source format '{}'.".format(should_be_floatable,
                                                file_size_text, distro_url[:-5], dl["file"])) from ve

            logging.debug("Captured filesize for '{}' as '{}'".format(distro_url,
                            str(this_distribution.byteSize)))

            # We'll get the mediaType from the file extension
            file_types = {
                ".csv": CSV,
                ".xlsx": Excel,
                ".ods": ODS,
                ".csdb": CSDB
            }
            for ft in file_types:
                if download_url.endswith(ft):
                    this_distribution.mediaType = file_types[ft]

            # inherit metadata from the dataset where it hasn't explicitly been changed
            this_distribution.title = scraper.dataset.title
            this_distribution.description = scraper.dataset.description
            this_distribution.contactPoint = "mailto:" + contact_dict["email"]

            logging.debug("Created distribution for download '{}'.".format(download_url))
            scraper.distributions.append(this_distribution)

    # boiler plate
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'


# depreciated, but keeping it is an optional so we don't break the world
def depreciated_scraper(scraper, tree):
    scraper.dataset.title = tree.xpath(
        "//h1/text()")[0].strip()
    scraper.dataset.issued = parse(tree.xpath(
        "//span[starts-with(text(),'Release date:')]/parent::node()/text()")[1].strip()).date()
    user_requested = tree.xpath(
        "//h2[starts-with(text(),'Summary of request')]"
    )

    if len(user_requested) > 0:
        scraper.dataset.identifier = tree.xpath(
            "//span[starts-with(text(), 'Reference number:')]/parent::node()/text()")[1].strip()
        scraper.dataset.comment = tree.xpath(
            "//h2[starts-with(text(), 'Summary of request')]/following-sibling::p/text()")[0].strip()
        distribution_link = tree.xpath(
            "//h2[starts-with(text(), 'Download associated with request')]/following-sibling::*/descendant::a")
        if len(distribution_link) > 0:
            distribution = Distribution(scraper)
            distribution.downloadURL = urljoin(scraper.uri, distribution_link[0].get('href'))
            distribution.title = distribution_link[0].text
            distribution_info = distribution_link[0].xpath(
                "following-sibling::text()")
            if len(distribution_info) > 0:
                info_text = distribution_info[0].strip()
                info_re = re.compile(r'\(([0-9\.])+\s+([kMG]B)\s+(xls|ods|pdf)\)')
                info_match = info_re.match(info_text)
                if info_match is not None:
                    size, units, file_type = info_match.groups()
                    if units == 'kB':
                        distribution.byteSize = size * 1024
                    elif units == 'MB':
                        distribution.byteSize = size * 1000000
                    if file_type == 'xls':
                        distribution.mediaType = Excel
                    elif file_type == 'ods':
                        distribution.mediaType = ODS
                    else:
                        distribution.mediaType, encoding = mimetypes.guess_type(distribution.downloadURL)
            scraper.distributions.append(distribution)
    else:
        try:
            scraper.dataset.updateDueOn = parse(tree.xpath(
                "//span[starts-with(text(),'Next release:')]/parent::node()/text()")[1].strip()).date()
        except ValueError as e:
            logging.warning('Unexpected "next release" field: ' + str(e))
        except IndexError:
            logging.warning('Unable to find "next release" field')
        try:
            mailto = tree.xpath(
                "//span[starts-with(text(),'Contact:')]/following-sibling::a[1]/@href")[0].strip()
            # guard against extraneous, invalid spaces
            scraper.dataset.contactPoint = re.sub(r'^mailto:\s+', 'mailto:', mailto)
        except IndexError:
            logging.warning('Unable to find "contact" field.')
        scraper.dataset.comment = tree.xpath(
            "//h2[starts-with(text(),'About this dataset')]/following-sibling::p/text()")[0].strip()

        for anchor in tree.xpath("//a[starts-with(@title, 'Download as ')]"):
            distribution = Distribution(scraper)
            distribution.downloadURL = urljoin(scraper.uri, anchor.get('href'))
            type_size_re = re.compile(r'([^(]*)\(([0-9.]+)\s+([^s]+)\)')
            type_size_match = type_size_re.match(anchor.text)
            if type_size_match is not None:
                typ, size, mult = type_size_match.groups()
                if mult == 'kB':
                    distribution.byteSize = float(size) * 1024
                elif mult == 'MB':
                    distribution.byteSize = float(size) * 1000000
                else:
                    distribution.byteSize = float(size)
                if typ.strip() == 'csv':
                    distribution.mediaType = CSV
                elif typ.strip() == 'xlsx':
                    distribution.mediaType = Excel
                elif typ.strip() == 'ods':
                    distribution.mediaType = ODS
                elif typ.strip() == 'structured text':
                    distribution.mediaType = CSDB
                else:
                    distribution.mediaType, encoding = mimetypes.guess_type(distribution.downloadURL)
            distribution.title = scraper.dataset.title
            scraper.distributions.append(distribution)
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
    scraper.dataset.license = tree.xpath(
        "//div[@class='footer-license']//a")[0].get('href')

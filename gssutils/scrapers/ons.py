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

def prefered_distribution_type(list_of_urls):
    """
    Helper function, where a distribution is available in multiple formats we need to pick one.
    # TODO: something of this ilk probably makes more sense as a global resource

    For now, I'm going with a preference of excel over csv and blow up for neither. But we might
    need to be a bit cleverer than that.

    :param list_of_urls:     list of truncated url endpoints with different formats
    :return use_me:          the chosen truncated url endpoint
    """

    reverse_ordered_suffix_preferences = [".csv", "xls", ".xlsx"]
    use_me = None
    for url_in_dict in list_of_urls:
        url = next(iter(url_in_dict.values()))
        for prefered_suffix in reverse_ordered_suffix_preferences:
            if url.endswith(prefered_suffix):
                use_me = url

    if use_me == None:
        raise ValueError("Aborting operation. Could not find a supported type from '{}' in" \
                "any of '{}'.".format(",".join(reverse_ordered_suffix_preferences), ",".join(list_of_urls)))

    return use_me


def scrape(scraper, tree):
    """
    The ONS pages vary a bit, they're (nearly!) all availible in json but they have distinct
    'types'. Rather than trying to account for the journey from every single type that we might
    start from (possible, but spagetti), I'm putting in a switch.

    Basically, you'll get the handler for the page type you've provided. Or you'll get a
    exception telling you we don't handle it.

    :param scraper:     The Scraper Object
    :param tree:        an lxml tree of the initial scrape
    :return:
    """

    # If we can't load it as json we'll have to have to assume it's coming from an older recipe,
    # so we'll throw a depreciation warning and use the old scraper.
    try:
        p = tree.xpath("//p/text()")[0].strip()
        initial_page = json.loads(p)
    except:
        scraper.logger.warning("This is not json-able content. Attempting to parse with depreciated html scraper.")
        depreciated_scraper(scraper, tree)
        return

    # note - add as needed
    page_handlers = {
        "dataset_landing_page": onshandler_dataset_landing_page
    }

    page_type = initial_page["type"]

    if page_type not in page_handlers:
        raise ValueError("Aborting. The ONS scraper does not handle ./data pages of type: " + page_type)

    scraper.logger.debug("Calling handler for page type: " + page_type)

    handler = page_handlers[page_type]
    handler(scraper, initial_page)


def onshandler_dataset_landing_page(scraper, landing_page):
    """
    This is the handler for the page type of "dataset_landing_page"

    The intention is to get the basic metadata from this page, then look at the provided
    /current link to get the specific distributions with distribution-level metadata

    :param scraper:         the Scraper object
    :param landing_page:    the /data representation of this page
    :return:
    """

    # sanity check, in case we do something silly
    if landing_page["type"] != "dataset_landing_page":
        raise ValueError("Aborting. Scraper is expecting to start on page of type 'dataset_landing_page'" \
                "not '{}'.".format(landing_page["type"]))

    # sanity check, in case they do something silly
    if len(landing_page["datasets"]) != 1:
        raise ValueError("Aborting. More than one dataset linked on a dataset landing page: {}." \
                         .format(",".join(landing_page["datasets"])))

    # Acquire basic metadata from dataset_landing_page
    scraper.dataset.title = landing_page["description"]["title"]
    scraper.dataset.issued = landing_page["description"]["releaseDate"] # TODO time format

    # Get json "scrape" of the ./current page
    page_url = ONS_PREFIX+landing_page["datasets"][0]["uri"]+"/data"
    r = requests.get(page_url)
    if r.status_code != 200:
        raise ValueError("Scrape of url '{}' failed with status code {}.".format(page_url, r.status_code))

    current_dataset_page = r.json() # dict-ify

    distributions_url_list = [ONS_PREFIX + landing_page["datasets"][0]["uri"]+"/data"]
    for version_as_dict in current_dataset_page["versions"]:
        distributions_url_list.append(ONS_PREFIX+version_as_dict["uri"]+"/data")

    # now we've got a list of distributions as urls, lets create those objects
    for distro_url in distributions_url_list:
        scraper.logger.debug("Identified distribution url, building distribution object for: " + distro_url)

        r = requests.get(distro_url)
        if r.status_code != 200:
            raise ValueError("Aborting. Scraper unable to acquire the page: "+ distro_url)

        this_page = r.json()    # dict-ify

        # Distribution object to represent this distribution
        this_distribution = Distribution(scraper)

        # Get the download url (use our preference where there're multiple formats)
        distribution_formats = this_page["downloads"]
        chosen_format_endpoint = prefered_distribution_type(distribution_formats)
        download_url = ONS_DOWNLOAD_PREFIX+this_page["uri"]+"/"+chosen_format_endpoint
        this_distribution.downloadURL = download_url
        this_distribution.mediaType = download_url.split('.')[1]

        # Get file size
        """
        # TODO - this is a bit nasty.
        
        It's because my old pal zebedee (ONS content file server) is resisting all attempts to give
        out file information beyond letting you download the whole thing.
        
        Am having to switch back to the html page and nip out the hard coded file size.
        """
        lines_in_html_page = [x for x in requests.get(distro_url[:-5]).text.split("\n")]
        file_size_text = None
        for i in range(0, len(lines_in_html_page)):
            if 'data-gtm-date="Latest"' in lines_in_html_page[i]:
                file_size_text = lines_in_html_page[i+2]
                break
        this_distribution.byteSize = float(file_size_text[1:].split(" ")[0]) * 1000

        scraper.distributions.append(this_distribution)

    # boiler plate
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'


# depreciated, but keeping it is an optional so we don't break the world
def depreciated_scraper(scraper, tree):
    scraper.dataset.title = tree.xpath(
        "//h1/text()")[0].strip()
    scraper.dataset.issued = parse(tree.xpath(
        "//span[text() = 'Release date: ']/parent::node()/text()")[1].strip()).date()
    user_requested = tree.xpath(
        "//h2[text() = 'Summary of request']"
    )

    if len(user_requested) > 0:
        scraper.dataset.identifier = tree.xpath(
            "//span[text() = 'Reference number: ']/parent::node()/text()")[1].strip()
        scraper.dataset.comment = tree.xpath(
            "//h2[text() = 'Summary of request']/following-sibling::p/text()")[0].strip()
        distribution_link = tree.xpath(
            "//h2[text()='Download associated with request ']/following-sibling::*/descendant::a")
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
                "//span[text() = 'Next release: ']/parent::node()/text()")[1].strip()).date()
        except ValueError as e:
            logging.warning('Unexpected "next release" field: ' + str(e))
        except IndexError:
            logging.warning('Unable to find "next release" field')
        try:
            mailto = tree.xpath(
                "//span[text() = 'Contact: ']/following-sibling::a[1]/@href")[0].strip()
            # guard against extraneous, invalid spaces
            scraper.dataset.contactPoint = re.sub(r'^mailto:\s+', 'mailto:', mailto)
        except IndexError:
            logging.warning('Unable to find "contact" field.')
        scraper.dataset.comment = tree.xpath(
            "//h2[text() = 'About this dataset']/following-sibling::p/text()")[0].strip()

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

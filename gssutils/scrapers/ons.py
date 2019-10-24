import logging
import mimetypes
import re
from urllib.parse import urljoin

from dateutil.parser import parse

from gssutils.metadata import Distribution, Excel, ODS, CSV, CSDB

import requests

import json

ONS_PREFIX = "https://www.ons.gov.uk"
ONS_DOWNLOAD_PREFIX = ONS_PREFIX+"/file?uri="


def scrape(scraper, uri):
    """
    This is the handler for the page type of "dataset_landing_page"

    The intention is to get the basic metadata from this page, then look at the provided
    /current link (and its "previous version" info) and create a .distribution for each
    format type of each previous version of said dataset.

    :param scraper:         the Scraper object
    :param landing_page:    lxml etree
    :return:
    """

    # If we can't load it as json we'll have to have to assume it's coming from an older recipe,
    # so we'll throw a depreciation warning and use the old scraper.

    r = requests.get(uri + "/data")
    if r.status_code != 200:
        raise ValueError("Aborting. Issue encountered while attempting to scrape '{}'. Http code" \
                         "returned was '{}.".format(uri+"/data", r.status_code))
    try:
        landing_page = r.json()
    except Exception as e:
        raise ValueError("Aborting operation This is not json-able content.") from e

    # throw an exception if it's a json page type we don't handle
    page_type = landing_page["type"]
    if page_type.strip() != "dataset_landing_page":
        raise ValueError("Aborting. The ONS scraper handles pages of /data json type " \
                         "'dataset_landing_page', not {}."+ page_type)

    # Acquire basic metadata from the dataset_landing_page
    scraper.dataset.title = landing_page["description"]["title"].strip()
    scraper.dataset.description = landing_page["description"]["metaDescription"]
    scraper.dataset.issued = parse(landing_page["description"]["releaseDate"]).date()
    scraper.dataset.comment = landing_page["description"]["summary"].strip()

    # next release is sometimes blank or a string, so use a conditional before parsing time
    if landing_page["description"]["nextRelease"] != "To be announced" and \
            landing_page["description"]["nextRelease"] != "":
        scraper.dataset.updateDueOn = parse(landing_page["description"]["nextRelease"])


    # get contact info now, as it's only available via json at the landing_page level
    # note, adding mailto: prefix so the property gets correctly identified by metadata.py
    contact_dict = landing_page["description"]["contact"]
    scraper.dataset.contactPoint = "mailto:"+contact_dict["email"]

    # Get json "scrape" of the "datasets"
    for dataset_page_url in landing_page["datasets"]:

        dataset_page_json_url = ONS_PREFIX+dataset_page_url["uri"]+"/data"
        r = requests.get(dataset_page_json_url)
        if r.status_code != 200:
            raise ValueError("Scrape of url '{}' failed with status code {}." \
                             .format(dataset_page_json_url, r.status_code))

        this_dataset_page = r.json() # dict-ify

        # start a dictionary of dataset versions (to hold current + all previous) as
        # {url: release_date}, start with just the current/latest version
        versions_dict = {ONS_PREFIX + this_dataset_page["uri"]+"/data":
                                        landing_page["description"]["releaseDate"]}

        # then add all the older version to that dictionary
        for version_as_dict in this_dataset_page["versions"]:
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
                this_distribution.issued = parse(release_date.strip()).date()

                assert 'file' in dl.keys(), "Aborting, expecting dict with 'file' key. Instead " \
                        + "we got: {}.".format(str(dl))

                download_url = ONS_DOWNLOAD_PREFIX+this_page["uri"]+"/"+dl["file"]
                this_distribution.downloadURL = download_url
                this_distribution.mediaType, encoding = mimetypes.guess_type(this_distribution.downloadURL)

                # inherit metadata from the dataset where it hasn't explicitly been changed
                this_distribution.title = scraper.dataset.title
                this_distribution.description = scraper.dataset.description
                this_distribution.contactPoint = scraper.dataset.contactPoint

                logging.debug("Created distribution for download '{}'.".format(download_url))
                scraper.distributions.append(this_distribution)

        # boiler plate
        scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'


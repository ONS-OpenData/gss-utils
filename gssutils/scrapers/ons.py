import logging
import mimetypes
import re
from urllib.parse import urljoin

from dateutil.parser import parse

from gssutils.metadata import Distribution, Excel, ODS, CSV, ExcelOpenXML, CSDB

import requests

import json

ONS_PREFIX = "https://www.ons.gov.uk"
ONS_DOWNLOAD_PREFIX = ONS_PREFIX+"/file?uri="


def scrape(scraper, uri):
    """
    This is json scraper for ons.gov.uk pages

    This scraper will attempt to gather metadata from "standard" fields shared across page types
    then drop into page-type specific handlers.

    :param scraper:         the Scraper object
    :param landing_page:    the provided url
    :return:
    """

    r = requests.get(uri + "/data")
    if r.status_code != 200:
        raise ValueError("Aborting. Issue encountered while attempting to scrape '{}'. Http code" \
                         " returned was '{}.".format(uri+"/data", r.status_code))
    try:
        landing_page = r.json()
    except Exception as e:
        raise ValueError("Aborting operation This is not json-able content.") from e

    # Acquire basic metadata from the dataset_landing_page
    scraper.dataset.title = landing_page["description"]["title"].strip()

    scraper.dataset.description = landing_page["description"]["metaDescription"]
    scraper.dataset.issued = parse(landing_page["description"]["releaseDate"]).date()

    # comments are not always in the same place...
    page_type = landing_page["type"]
    if page_type == "dataset_landing_page":
        scraper.dataset.comment = landing_page["description"]["summary"].strip()
    else:
        scraper.dataset.comment = landing_page["markdown"][0]

    # not all page types have a next Release date field
    try:
        # next release is sometimes blank or a string, so use a conditional before parsing time
        if landing_page["description"]["nextRelease"] != "To be announced" and \
                landing_page["description"]["nextRelease"] != "":
            scraper.dataset.updateDueOn = parse(landing_page["description"]["nextRelease"])
    except KeyError:
        logging.debug("no description.nextRelease key in json, skipping")

    # not all page types have contact field
    try:
        contact_dict = landing_page["description"]["contact"]
        scraper.dataset.contactPoint = "mailto:"+contact_dict["email"].strip()
    except KeyError:
        logging.debug("no description.contact key in json, skipping")

    # boiler plate
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
    scraper.dataset.licence = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"

    # From this point the json structure can vary based on the page type
    # so we're switching to a handler for each
    page_handlers = {
        "static_adhoc": handler_static_adhoc,
        "dataset_landing_page": handler_dataset_landing_page
    }

    if page_type not in page_handlers.keys():
        raise ValueError("Aborting operation. Scraper cannot handle page of type '{}'.".format(page_type))

    page_handlers[page_type](scraper, landing_page)


def handler_static_adhoc(scraper, landing_page):

    for download in landing_page["downloads"]:

        title = download["title"]
        file = download["file"]

        # Distribution object to represent this distribution
        this_distribution = Distribution(scraper)
        this_distribution.issued = parse(landing_page["description"]["releaseDate"]).date()

        download_url = ONS_DOWNLOAD_PREFIX + landing_page["uri"] + "/" + file
        this_distribution.downloadURL = download_url
        this_distribution.mediaType, encoding = mimetypes.guess_type(this_distribution.downloadURL)

        this_distribution.title = title

        # inherit metadata from the dataset where it hasn't explicitly been changed
        this_distribution.description = scraper.dataset.description

        logging.debug("Created distribution for download '{}'.".format(download_url))
        scraper.distributions.append(this_distribution)

def handler_dataset_landing_page(scraper, landing_page):

    # Get json "scrape" of the "datasets"
    for dataset_page_url in landing_page["datasets"]:

        dataset_page_json_url = ONS_PREFIX+dataset_page_url["uri"]+"/data"
        r = requests.get(dataset_page_json_url)
        if r.status_code != 200:
            raise ValueError("Scrape of url '{}' failed with status code {}." \
                             .format(dataset_page_json_url, r.status_code))

        this_dataset_page = r.json() # dict-ify

        # start a list of dataset versions (to hold current + all previous) as
        # {start with just the current/latest version
        versions_list = [ONS_PREFIX + this_dataset_page["uri"]+"/data"]

        # then add all the older version to that dictionary
        for version_as_dict in this_dataset_page["versions"]:
            versions_list.append(ONS_PREFIX+version_as_dict["uri"]+"/data")

        # iterate through the lot, creating a distribution objects for each
        # then add it to the list scraper.distributions[]
        for version_url in versions_list:
            logging.debug("Identified distribution url, building distribution object for: " + version_url)

            r = requests.get(version_url)
            if r.status_code != 200:
                raise ValueError("Aborting. Scraper unable to acquire the page: "+ version_url)

            this_page = r.json()    # dict-ify

            # Get the download urls, if there's more than 1,each forms a separate distribution
            distribution_formats = this_page["downloads"]
            for dl in distribution_formats:

                release_date = this_page["description"]["releaseDate"]

                # Distribution object to represent this distribution
                this_distribution = Distribution(scraper)
                this_distribution.issued = parse(release_date.strip()).date()

                assert 'file' in dl.keys(), "Aborting, expecting dict with 'file' key. Instead " \
                        + "we got: {}.".format(str(dl))

                download_url = ONS_DOWNLOAD_PREFIX+this_page["uri"]+"/"+dl["file"].strip()
                this_distribution.downloadURL = download_url

                # guess media type, check None as csdb with url as the guess is failing
                media_type, encoding = mimetypes.guess_type(this_distribution.downloadURL)
                if download_url.endswith(".csdb"):
                    media_type = CSDB

                this_distribution.mediaType = media_type

                # inherit metadata from the dataset where it hasn't explicitly been changed
                this_distribution.title = scraper.dataset.title
                this_distribution.description = scraper.dataset.description
                this_distribution.contactPoint = scraper.dataset.contactPoint

                logging.debug("Created distribution for download '{}'.".format(download_url))
                scraper.distributions.append(this_distribution)

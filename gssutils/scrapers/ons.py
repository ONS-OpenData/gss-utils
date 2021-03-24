import logging

from csv import DictReader
from io import StringIO

from dateutil import tz
from dateutil.parser import parse, isoparse
from urllib.parse import urlparse, urlunparse

from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import Excel, ODS, CSV, ExcelOpenXML, CSDB

import mimetypes

# save ourselves some typing later
ONS_PREFIX = "https://www.ons.gov.uk"
ONS_DOWNLOAD_PREFIX = ONS_PREFIX + "/file?uri="
ONS_TOPICS_CSV = 'https://gss-cogs.github.io/ref_common/reference/codelists/ons-topics.csv'


def scrape(scraper, tree):
    """
    This is json scraper for ons.gov.uk pages
    This scraper will attempt to gather metadata from "standard" fields shared across page types
    then drop into page-type specific handlers.
    :param scraper:         the Scraper object
    :param landing_page:    the provided url
    :return:
    """

    # So we start from an ons url and append /data to it, to get json as per the following:
    # https://www.ons.gov.uk/businessindustryandtrade/internationaltrade/datasets/uktradeingoodsbyclassificationofproductbyactivity/data
    # any issues getting it, or if we can't load the response into json - throw an error
    r = scraper.session.get(scraper.uri + "/data")
    if r.status_code != 200:
        raise ValueError("Aborting. Issue encountered while attempting to scrape '{}'. Http code"
                         " returned was '{}.".format(scraper.uri + "/data", r.status_code))
    try:
        landing_page = r.json()
    except Exception as e:
        raise ValueError("Aborting operation This is not json-able content.") from e

    accepted_page_types = ["dataset_landing_page", "static_adhoc"]
    if landing_page["type"] not in accepted_page_types:
        raise ValueError("Aborting operation This page type is not supported.")

    # Acquire title and description from the page json
    # literally just whatever's in {"description": {"title": <THIS> }}
    # and {"description": {"metaDescription": <THIS> }}
    scraper.dataset.title = landing_page["description"]["title"].strip()
    scraper.dataset.description = landing_page["description"]["metaDescription"]

    # Same with date, but use parse_as_local_date() which converts to the right time type
    scraper.dataset.issued = parse_as_local_date(landing_page["description"]["releaseDate"])

    # each json page has a type, represented by the 'type' field in the json
    # the most common one for datasets is dataset_landing_page
    # if that's the page type we're looking at then the comment is in {"description": {"summary": <THIS> }}
    # otherwise, look in the markdown field (adhoc notes about a page)
    page_type = landing_page["type"]
    if page_type == "dataset_landing_page":
        scraper.dataset.comment = landing_page["description"]["summary"].strip()
    else:
        scraper.dataset.comment = landing_page["markdown"][0]

    # not all page types have a next Release date field, also - "to be announced" is useless as is a blank entry.
    # so if its present, not blank, and doesnt say "to be announced" get it as
    # {"description": {"nextRelease": <THIS> }} and parse() to time type
    # note: the reasons we're being this careful is the timer parser will throw an error for bad input
    # and kill the scrape dead.
    try:
        # TODO - a list of things that aren't a date won't scale. Put a real catch in if we get any more.
        if landing_page["description"]["nextRelease"] not in ["To be announced", "Discontinued", ""]:
            scraper.dataset.updateDueOn = parse(landing_page["description"]["nextRelease"], dayfirst=True)
    except KeyError:
        # if there's no such key in the dict, python will throw a key error. Catch and control it.
        # if we're skipping a field, we might want to know
        logging.debug("no description.nextRelease key in json, skipping")

    # not all page types have contact field so we need another catch
    # if the page does, get the email address as contact info.
    # stick "mailto:" on the start because metadata expects it.
    try:
        contact_dict = landing_page["description"]["contact"]
        scraper.dataset.contactPoint = "mailto:" + contact_dict["email"].strip()
    except KeyError:
        # if we're skipping a field, we might want to know
        logging.debug("no description.contact key in json, skipping")

    # boiler plate
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
    scraper.dataset.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"

    # theme isn't provided explicitly in the JSON, so we need to use the URL path
    # and match it against the taxonomy codelist from GitHub
    topics_response = scraper.session.get(
        ONS_TOPICS_CSV,
        stream=True
    )
    topics_reader = DictReader(StringIO(topics_response.content.decode('utf-8')))
    prefix = None
    parsed_uri = urlparse(scraper.uri)
    for row in topics_reader:
        if parsed_uri.path.startswith(row['Path']):
            if prefix is None or len(prefix) < len(row['Path']):
                prefix = row['Path']

    scraper.dataset.theme = urlunparse(parsed_uri._replace(path=prefix))

    # From this point the json structure vary based on the page type
    # so we're switching to page-type specific handling
    page_handlers = {
        "static_adhoc": handler_static_adhoc,
        "dataset_landing_page": handler_dataset_landing_page
    }

    # if the page "type" isn't one we do, blow up
    if page_type not in page_handlers.keys():
        raise ValueError("Aborting operation. Scraper cannot handle page of type '{}'.".format(page_type))

    page_handlers[page_type](scraper, landing_page, tree)


def parse_as_local_date(dt: str):
    """
    Dates provided by the /data JSON are actually given as date times using ISO 8601 with UTC, so during
    British Summer Time, will be one hour before midnight the day before.
    We can account for this if we figure out the datetime in the Europe/London timezone and then take the date.
    """
    tz_ons = tz.gettz('Europe/London')
    return isoparse(dt).astimezone(tz_ons).date()


def handler_dataset_landing_page_fallback(scraper, this_dataset_page, tree):
    """
    At time of writing there's an issue with the latest version of datasets 404'ing on the
    versions page.
    
    this function will create what the latest version should be, using the information on the
    base dataset landing page.
    """

    logging.warning("Using fallback logic to scrape latest distribution from dataset landing page (rather "
                    "than previous page). This scrape will only have a single distribution of xls.")

    this_distribution = Distribution(scraper)

    release_date = this_dataset_page["description"]["releaseDate"]
    this_distribution.issued = parse(release_date.strip()).date()

    # gonna have to go via html ...
    download_url = tree.xpath("//a[text()='xls']/@href")
    this_distribution.downloadURL = download_url

    media_type = Excel
    this_distribution.mediaType = media_type

    this_distribution.title = scraper.dataset.title
    this_distribution.description = scraper.dataset.description
    this_distribution.contactPoint = scraper.dataset.contactPoint

    logging.debug("Created distribution for download '{}'.".format(download_url))
    scraper.distributions.append(this_distribution)


def handler_dataset_landing_page(scraper, landing_page, tree):
    # A dataset landing page has uri's to one or more datasets via it's "datasets" field.
    # We need to look at each in turn, this is an example one as json:
    # https://www.ons.gov.uk//businessindustryandtrade/internationaltrade/datasets/uktradeingoodsbyclassificationofproductbyactivity/current/data
    for dataset_page_url in landing_page["datasets"]:

        # Get the page as json. Throw an information error if we fail for whatever reason
        dataset_page_json_url = ONS_PREFIX + dataset_page_url["uri"] + "/data"
        r = scraper.session.get(dataset_page_json_url)
        if r.status_code != 200:
            raise ValueError("Scrape of url '{}' failed with status code {}." \
                             .format(dataset_page_json_url, r.status_code))

        # get the response json into a python dict
        this_dataset_page = r.json()

        # create a list, with each entry a dict of a versions url and update date
        versions_dict_list = []

        # Where the dataset is versioned, use the versions as the distributions
        try:
            all_versions = this_dataset_page["versions"]
        except KeyError:
            all_versions = []

        # Release dates:
        # --------------
        # ONS does this odd thing where each version on the /data api
        # has a updateDate field which is actually the date THE DATA
        # WAS SUPERCEDED (so the release fate of the NEXT version of the data).
        # ......this takes a bit of unpicking.

        # If no initial release date for the dataset has been provided
        # We're just going to ignore v1, we don't have a use for it
        # and with no provided release date ... not a lot to be done
        initial_release = this_dataset_page["description"].get("releaseDate", None)

        next_release = None
        # Where there's multiple versions, iterate all and populate a list
        if len(all_versions) != 0:
            try:
                for version_as_dict in all_versions:
                    if next_release is None:
                        release_date = initial_release
                    else:
                        release_date = next_release

                    if release_date is not None:
                        versions_dict_list.append({
                            "url": ONS_PREFIX + version_as_dict["uri"] + "/data",
                            "issued": release_date
                        })
                    next_release = version_as_dict["updateDate"]
            except KeyError:
                logging.debug("No older versions found for {}.".format(dataset_page_url))

        # Add the current release
        versions_dict_list.append({
            "url": ONS_PREFIX + this_dataset_page["uri"] + "/data",
            "issued": initial_release if next_release is None else next_release
        })

        # NOTE - we've had an issue with the very latest dataset not being updated on the previous versions
        # page (the page we're getting the distributions from) so we're taking the details for it from
        # the landing page to use as a fallback in that scenario.

        # iterate through the lot, we're aiming to create at least one distribution object for each
        for i, version_dict in enumerate(versions_dict_list):

            version_url = version_dict["url"]
            issued = version_dict["issued"]

            logging.debug("Identified distribution url, building distribution object for: " + version_url)

            r = scraper.session.get(version_url)
            if r.status_code != 200:

                # If we've got a 404 on the latest, fallback on using the details from the
                # landing page instead
                if r.status_code == 404 and i == len(versions_dict_list) - 1:
                    handler_dataset_landing_page_fallback(scraper, this_dataset_page, tree)
                    continue
                else:
                    raise Exception("Scraper unable to acquire the page: {} with http code {}."
                                    .format(version_url, r.status_code))

            # get the response json into a python dict
            this_page = r.json()

            # Get the download urls, if there's more than 1 format of this version of the dataset
            # each forms a separate distribution
            distribution_formats = this_page["downloads"]
            for dl in distribution_formats:

                # Create an empty Distribution object to represent this distribution
                # from here we're just looking to fill in it's fields
                this_distribution = Distribution(scraper)
                this_distribution.issued = parse_as_local_date(issued)

                # I don't trust dicts with one constant field (they don't make sense), so just in case...
                try:
                    download_url = ONS_DOWNLOAD_PREFIX + this_page["uri"] + "/" + dl["file"].strip()
                    this_distribution.downloadURL = download_url
                except:
                    # Throw a warning and abandon this distribution, ff we don't have a downloadURL it's not much use
                    logging.warning("Unable to create complete download url for {} on page {}"
                                    .format(dl, version_url))
                    continue

                # we've had some issues with type-guessing so we're getting the media type
                # by checking the download url ending
                if download_url.endswith(".csdb"):
                    media_type = CSDB
                elif download_url.endswith(".csv"):
                    media_type = CSV
                elif download_url.endswith(".xlsx"):
                    media_type = Excel
                elif download_url.endswith(".ods"):
                    media_type = ODS
                else:
                    media_type, _ = mimetypes.guess_type(download_url)

                this_distribution.mediaType = media_type

                # inherit metadata from the dataset where it hasn't explicitly been changed
                this_distribution.title = scraper.dataset.title
                this_distribution.description = scraper.dataset.description

                logging.debug("Created distribution for download '{}'.".format(download_url))
                scraper.distributions.append(this_distribution)


def handler_static_adhoc(scraper, landing_page, tree):
    # A static adhoc is a one-off unscheduled release
    # These pages should be simpler and should lack the historical distributions

    for download in landing_page["downloads"]:

        title = download["title"]
        file = download["file"]

        # Create an empty Distribution object to represent this distribution
        # from here we're just looking to fill in it's fields
        this_distribution = Distribution(scraper)

        # if we can't get the release date, continue but throw a warning.
        try:
            this_distribution.issued = parse(landing_page["description"]["releaseDate"]).date()
        except KeyError:
            logging.warning("Unable to acquire or parse release date")

        download_url = ONS_DOWNLOAD_PREFIX + landing_page["uri"] + "/" + file
        this_distribution.downloadURL = download_url

        # TODO - we're doing this in two place, pull it out
        # we've had some issues with type-guessing so we're getting the media type
        # by checking the download url ending
        if download_url.endswith(".csdb"):
            media_type = CSDB
        elif download_url.endswith(".csv"):
            media_type = CSV
        elif download_url.endswith(".xlsx"):
            media_type = Excel
        elif download_url.endswith(".ods"):
            media_type = ODS
        else:
            media_type, _ = mimetypes.guess_type(download_url)
        this_distribution.mediaType = media_type

        this_distribution.title = title

        # inherit metadata from the dataset where it hasn't explicitly been changed
        this_distribution.description = scraper.dataset.description

        logging.debug("Created distribution for download '{}'.".format(download_url))
        scraper.distributions.append(this_distribution)

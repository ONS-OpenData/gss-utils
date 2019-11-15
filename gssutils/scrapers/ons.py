import logging

from dateutil.parser import parse

from gssutils.metadata import Distribution, Excel, ODS, CSV, ExcelOpenXML, CSDB

import mimetypes

# save ourselves some typing later
ONS_PREFIX = "https://www.ons.gov.uk"
ONS_DOWNLOAD_PREFIX = ONS_PREFIX+"/file?uri="


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
        raise ValueError("Aborting. Issue encountered while attempting to scrape '{}'. Http code" \
                         " returned was '{}.".format(uri+"/data", r.status_code))
    try:
        landing_page = r.json()
    except Exception as e:
        raise ValueError("Aborting operation This is not json-able content.") from e

    # Acquire title and description from the page json
    # literally just whatever's in {"description": {"title": <THIS> }}
    # and {"description": {"metaDescription": <THIS> }}
    scraper.dataset.title = landing_page["description"]["title"].strip()
    scraper.dataset.description = landing_page["description"]["metaDescription"]

    # Same with date, but use parse() which converts to the right time type
    scraper.dataset.issued = parse(landing_page["description"]["releaseDate"]).date()

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
        if landing_page["description"]["nextRelease"] != "To be announced" and \
                landing_page["description"]["nextRelease"] != "":
            scraper.dataset.updateDueOn = parse(landing_page["description"]["nextRelease"])
    except KeyError:
        # if there's no such key in the dict, python will throw a key error. Catch and control it.
        # if we're skipping a field, we might want to know
        logging.debug("no description.nextRelease key in json, skipping")

    # not all page types have contact field so we need another catch
    # if the page does, get the email address as contact info.
    # stick "mailto:" on the start because metadata.py expects it.
    try:
        contact_dict = landing_page["description"]["contact"]
        scraper.dataset.contactPoint = "mailto:"+contact_dict["email"].strip()
    except KeyError:
        # if we're skipping a field, we might want to know
        logging.debug("no description.contact key in json, skipping")

    # boiler plate
    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
    scraper.dataset.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"

    # From this point the json structure vary based on the page type
    # so we're switching to page-type specific handling
    page_handlers = {
        "static_adhoc": handler_static_adhoc,
        "dataset_landing_page": handler_dataset_landing_page
    }

    # if the page "type" isn't one we do, blow up
    if page_type not in page_handlers.keys():
        raise ValueError("Aborting operation. Scraper cannot handle page of type '{}'.".format(page_type))

    page_handlers[page_type](scraper, landing_page)


def handler_dataset_landing_page(scraper, landing_page):

    # A dataset landing page has uri's to one or more datasets via it's "datasets" field.
    # We need to look at each in turn, this is an example one as json:
    # https://www.ons.gov.uk//businessindustryandtrade/internationaltrade/datasets/uktradeingoodsbyclassificationofproductbyactivity/current/data
    for dataset_page_url in landing_page["datasets"]:

        # Get the page as json. Throw an information error if we fail for whatever reason
        dataset_page_json_url = ONS_PREFIX+dataset_page_url["uri"]+"/data"
        r = scraper.session.get(dataset_page_json_url)
        if r.status_code != 200:
            raise ValueError("Scrape of url '{}' failed with status code {}." \
                             .format(dataset_page_json_url, r.status_code))

        # get the response json into a python dict
        this_dataset_page = r.json()

        # start a list of dataset versions (to hold current + all previous) as a list
        # we'll start with just the current/latest version
        versions_list = [ONS_PREFIX + this_dataset_page["uri"]+"/data"]

        # if there are older versions of this datasets availible.
        # iterate and add their uri's to the versions list
        try:
            for version_as_dict in this_dataset_page["versions"]:
                versions_list.append(ONS_PREFIX+version_as_dict["uri"]+"/data")
        except KeyError:
            logging.debug("No older versions found for {}.".format(dataset_page_url))

        # iterate through the lot, we're aiming to create at least one distribution object for each
        for version_url in versions_list:
            logging.debug("Identified distribution url, building distribution object for: " + version_url)

            r = scraper.session.get(version_url)
            if r.status_code != 200:
                raise ValueError("Aborting. Scraper unable to acquire the page: {} with http code {}." \
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

                # Every distribution SHOULD have a release date, but it seems they're not
                # always included. If it happens continue but throw a warning.
                try:
                    release_date = this_page["description"]["releaseDate"]
                    this_distribution.issued = parse(release_date.strip()).date()
                except KeyError:
                    logging.warning("Download {}. Of datasset versions {} of dataset {} does not have "
                                "a release date".format(distribution_formats, version_url, dataset_page_url))

                # I don't trust dicts with one constant field (they don't make sense), so just in case...
                try:
                    download_url = ONS_DOWNLOAD_PREFIX + this_page["uri"] + "/" + dl["file"].strip()
                    this_distribution.downloadURL = download_url
                except:
                    # raise up this time. If we don't have a downloadURL it's not much use
                    raise ValueError("Unable to create complete download url for {} on page {}" \
                                     .format(dl, version_url))

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
                this_distribution.contactPoint = scraper.dataset.contactPoint

                logging.debug("Created distribution for download '{}'.".format(download_url))
                scraper.distributions.append(this_distribution)


def handler_static_adhoc(scraper, landing_page):

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

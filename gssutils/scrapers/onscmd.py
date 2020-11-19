import logging

from dateutil.parser import parse

from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import CSV


def request_json_data(scraper, uri):
    """
    A simple helper to return a dict when given the url of a json endpoint
    """
    r = scraper.session.get(uri)
    if r.status_code != 200:
        raise ValueError("Failed to get url '{}' with status code {}.".format(uri, r.status_code))

    return r.json()


def scrape(scraper, tree):
    """
    This is a scraper intended to use the ONS cmd (customise my data) functionality.

    :param scraper:         the Scraper object
    :param landing_page:    lxml tree
    :return:
    """

    dataset_document = request_json_data(scraper, scraper.uri)

    scraper.dataset.title = dataset_document["id"]
    scraper.dataset.description = dataset_document["description"]

    # Need to get issued from the assciated publication
    publication_document = request_json_data(scraper, dataset_document["publications"][0]["href"]+"/data")
    scraper.dataset.issued = parse(publication_document["description"]["releaseDate"])

    # Only take next release it its a date
    try:
        next_release = parse(dataset_document["next_release"])
        scraper.dataset.updateDueOn = next_release
    except:
        pass  # it's fine, "unknown" etc

    # Theoretically you can have more than one contact, but I'm just taking the first
    scraper.dataset.contactPoint = "mailto:"+dataset_document["contacts"][0]["email"].strip()

    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
    scraper.dataset.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"

    edition_documents = request_json_data(scraper, scraper.uri+"/editions")

    for edition_document in edition_documents["items"]:
        
        edition_name = edition_document["edition"]

        version_documents = request_json_data(scraper, edition_document["links"]["versions"]["href"])

        for version_document in version_documents["items"]:

            version_name = str(version_document["version"])

            this_distribution = Distribution(scraper)

            this_distribution.issued = version_document["release_date"]
            this_distribution.downloadURL = version_document["downloads"]["csv"]["href"]
            this_distribution.mediaType = CSV

            this_distribution.title = scraper.dataset.title + ", {}, version {}".format(edition_name ,version_name)
            this_distribution.description = scraper.dataset.description
            this_distribution.contactPoint = scraper.dataset.contactPoint

            logging.debug("Created distribution for download '{}'.".format(this_distribution.downloadURL))
            scraper.distributions.append(this_distribution)

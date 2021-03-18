import mimetypes

from dateutil.parser import parse
from lxml import html

from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import CSV

def assert_get_one(thing, name_of_thing):
    """
    Helper to assert we have one of a thing when we're expecting one of a thing, then
    return that one thing de-listified
    """
    assert len(thing) == 1, f'Aborting. Xpath expecting 1 "{name_of_thing}", got {len(thing)}'
    return thing[0]

def scrape(scraper, tree):
    """
    Scraper for https://www.lowcarboncontracts.uk/data-portal/dataset/*

    Example: https://www.lowcarboncontracts.uk/data-portal/dataset/actual-ilr-income
    """

    article = assert_get_one(tree.xpath('//article'), "article element")

    title_element = assert_get_one(article.xpath('./div/h1'), 'title element')
    scraper.dataset.title = title_element.text.strip()

    description_elements = article.xpath('./div/div/p')
    scraper.dataset.description = "\n\n".join([x.text.strip() for x in description_elements])

    issued_element = assert_get_one(article.xpath('./div/section/table/tbody/tr[1]/td/span'), "issued element")
    scraper.dataset.issued = parse(issued_element.text.split("(")[0].strip())

    scraper.dataset.license = "http://reference.data.gov.uk/id/open-government-licence"
    
    for resource in assert_get_one(article.xpath('./div/section[1]/ul[1]'), "resource list").xpath('./li/a'):

        distro = Distribution(scraper)

        url = f'https://www.lowcarboncontracts.uk/{resource.get("href")}'
        resp = scraper.session.get(url)
        if resp.status_code != 200:
            raise Exception(f'Failed to get url resource {url}')

        distro_tree = html.fromstring(resp.text)
        section = assert_get_one(distro_tree.xpath('/html[1]/body[1]/div[3]/div[1]/div[3]/section[1]'), "section of distro")
 
        distro_title_element = assert_get_one(section.xpath('./div/h1'), "distro title")
        distro.title = distro_title_element.text

        distro_description_element = assert_get_one(section.xpath('./div/div/blockquote[1]'), "distro description")
        distro.description = distro_description_element.text

        distro_download_url_element = assert_get_one(section.xpath('./div/p/a'), "download url")
        distro.downloadURL = distro_download_url_element.text

        # Note: issued is the one thing not in the "section" element, so xpathing the whole distro tree
        distro_issued_element = assert_get_one(distro_tree.xpath('//table[1]/tbody[1]/tr[2]/td[1]'), "issued")
        distro.issued = parse(distro_issued_element.text)
  
        media_type, _ = mimetypes.guess_type(distro.downloadURL)
        distro.mediaType = media_type if media_type is not None else CSV    # the default/not-specified offering is csv

        scraper.distributions.append(distro)
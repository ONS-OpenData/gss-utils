import mimetypes
import re
from urllib.parse import urljoin, urlparse
<<<<<<< HEAD
from urllib.request import Request, urlopen
=======
>>>>>>> 9383b6dc9af296064168e0d4e62b37d18218573c

from dateutil.parser import parse

from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution

<<<<<<< HEAD
from cachecontrol import CacheControl, serialize
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import LastModified
from datetime import datetime

import requests
=======
from datetime import datetime

>>>>>>> 9383b6dc9af296064168e0d4e62b37d18218573c

from lxml import html



def publications(scraper, tree):
	scraper.dataset.title = tree.xpath('.// *[@id="page-content"] / div[1] / div / header / div[1] / div / h1')[0].text

	scraper.dataset.description = \
	tree.xpath('.// *[@id="page-content"] / div[1] / div / header / div[2] / div[2] / div / p')[0].text

	try:
		pubDate = tree.xpath('// *[@id="page-content"] / div[1] / div / header / div[2] / div[1] / section / div[1] / span[2] / strong')[0].text
		scraper.dataset.issued = datetime.strptime(pubDate, '%d %b %Y').date()
	except:
		pass

	dists = tree.findall('.//*[@id="page-content"]/div[3]/div/div/div[2]/section')

	for entry in dists:
		distributions = entry.findall('.//*[@class="no-icon"]')
		for i in distributions:
			dist = Distribution(scraper)
			dist.title = i.text
			dist.downloadURL = urljoin("https://www.gov.scot", i.attrib['href'])
			dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
			if dist.mediaType in ['application/msword', 'application/pdf', 'None']:
				return
<<<<<<< HEAD
			elif dist.mediaType == None:
=======
			elif dist.mediaType is None:
>>>>>>> 9383b6dc9af296064168e0d4e62b37d18218573c
				return
			else:
				scraper.distributions.append(dist)

def collections(scraper, tree):

	scraper.dataset.title = tree.xpath('.// *[@id="page-content"] / header / div / div[1] / h1')[0].text

	scraper.dataset.description = tree.xpath('.// *[@id="page-content"] / header / div / div[3] / p')[0].text

	pubPages = tree.findall('.//ul[@class="collections-list"]')
	for page in pubPages:
		pages = page.findall('.//a')
		for i in pages:
			url = urljoin("https://www.gov.scot", i.attrib['href'])
			r = scraper.session.get(url)
			pubTree = html.fromstring(r.text)
			try:
				pubDate = pubTree.xpath('// *[@id="page-content"] / div[1] / div / header / div[2] / div[1] / section / div[1] / span[2] / strong')[0].text
				scraper.dataset.issued = pubDate
			except:
				pass

			dists = pubTree.xpath('//*[@id="page-content"]/div[3]/div/div/div[2]/section/div/div[2]/h3/a')

			for i in dists:
				dist = Distribution(scraper)
				dist.title = i.text
				dist.downloadURL = urljoin("https://www.gov.scot", i.attrib['href'])
				dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
				if dist.mediaType in ['application/msword', 'application/pdf', 'None']:
					pass
				elif dist.mediaType == None:
					pass
				else:
					scraper.distributions.append(dist)

def scrape(scraper, tree):
<<<<<<< HEAD

	r = scraper.session.get(scraper.uri)

	parse_object = urlparse(r.url)

	scraper.dataset.publisher = GOV['the-scottish-government']

	scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'

	if 'publications' in parse_object.path:
		publications(scraper, tree)
	elif 'collections' in parse_object.path:
		collections(scraper, tree)
	else:
		print('GovScot Scraper does not support given landing page')

"""

When provided with a GovScot landing page this will determine whther it is a publication page - which contains the dataset(s) and metadata -
or a collections page which contains links to many publications pages. 

If a publications link is provided it will take all the datasets on the publications page and turn them into distributions containing the dataURL and basic meta data.
If a collections link is provided then it will open each publications link on the page and go through each adding to the list of distributions whenever an excel/csv file is found.

"""

def scrape_old(scraper, tree):
=======
    """ Scrapes GovScot landing page.

    When provided with a GovScot landing page this will determine whether it is a publication page - which contains
    the dataset(s) and metadata - or a collections page which contains links to many publications pages.

    If a publications link is provided it will take all the datasets on the publications page and turn them into
    distributions containing the dataURL and basic meta data. If a collections link is provided then it will open
    each publications link on the page and go through each adding to the list of distributions whenever an excel/csv
    file is found.
    """

    r = scraper.session.get(scraper.uri)

    parse_object = urlparse(r.url)

    scraper.dataset.publisher = GOV['the-scottish-government']

    scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'

    if 'publications' in parse_object.path:
        publications(scraper, tree)
    elif 'collections' in parse_object.path:
        collections(scraper, tree)
    else:
        print('GovScot Scraper does not support given landing page')


def scrape_old(scraper, tree):
    """Deprecated scraper for 'https://www2.gov.scot/Topics/Statistics/Browse/' links."""

>>>>>>> 9383b6dc9af296064168e0d4e62b37d18218573c
    scraper.dataset.publisher = GOV['the-scottish-government']
    scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
    scraper.dataset.title = tree.xpath(
        "//div[@id='body2']//h2/text()")[0].strip()
    scraper.dataset.description = scraper.to_markdown(tree.xpath(
        "//div[@id='body2']//h2/following-sibling::div/child::div"))
    doctable = tree.xpath(
        "//table[contains(concat(' ', @class, ' '), ' dg file ')]")[0]
    for row in doctable.xpath('tr'):
        try:
            if row.xpath('th/text()')[0].strip() == 'File:':
                cell = row.xpath('td')[0]
                dist = Distribution(scraper)
                title_size_date = re.compile(r'(.*)\[([^,]+),\s+([0-9.]+)\s+([^:]+):\s([^\]]+)')
                match = title_size_date.match(cell.text_content())
                if match:
                    dist.title = match.group(1)
                    scraper.dataset.issued = parse(match.group(5), dayfirst=True).date()
                dist.downloadURL = urljoin(scraper.uri, cell.xpath('a/@href')[0])
                dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
                scraper.distributions.append(dist)
        except:
            break

"""

Depreciated scraper for 'https://www2.gov.scot/Topics/Statistics/Browse/' links

"""

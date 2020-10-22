import mimetypes
import re
from urllib.parse import urljoin, urlparse

from dateutil.parser import parse

from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import *

from datetime import datetime

from lxml import html

import logging

ACCEPTED_MIMETYPES = [ODS, Excel, ExcelOpenXML, ExcelTypes, ZIP, CSV, CSDB]

def publications(scraper, tree):

	scraper.dataset.title = tree.xpath('.// *[@id="page-content"] / div[1] / div / header / div[1] / div / h1')[0].text

	scraper.dataset.description = \
	tree.xpath('.// *[@id="page-content"] / div[1] / div / header / div[2] / div[2] / div / p')[0].text

	try:
		pubDate = tree.xpath('// *[@id="page-content"] / div[1] / div / header / div[2] / div[1] / section / div[1] / span[2] / strong')[0].text
		scraper.dataset.issued = parse(pubDate).date()
	except:
		pass

	dists = tree.findall('.//*[@id="page-content"]/div[3]/div/div/div[2]/section')

	for entry in dists:
		distributions = entry.findall('.//*[@class="no-icon"]')
		for element in distributions:
			dist = Distribution(scraper)
			dist.title = element.text
			dist.downloadURL = urljoin("https://www.gov.scot", element.attrib['href'])
			dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
			if dist.mediaType in ACCEPTED_MIMETYPES:
				scraper.distributions.append(dist)
			else:
				pass

def collections(scraper, tree):

	scraper.dataset.title = tree.xpath('.// *[@id="page-content"] / header / div / div[1] / h1')[0].text

	scraper.dataset.description = tree.xpath('.// *[@id="page-content"] / header / div / div[3] / p')[0].text

	pubPages = tree.findall('.//ul[@class="collections-list"]')
	for page in pubPages:
		pages = page.findall('.//a')
		for publication in pages:
			url = urljoin("https://www.gov.scot", publication.attrib['href'])
			r = scraper.session.get(url)
			if r.status_code != 200:
				raise Exception('Failed to get url {url}, with status code "{status_code}".'.format(url=url,status_code=r.status_code))
			pubTree = html.fromstring(r.text)
			try:
				pubDate = pubTree.xpath('// *[@id="page-content"] / div[1] / div / header / div[2] / div[1] / section / div[1] / span[2] / strong')[0].text
				scraper.dataset.issued = parse(pubDate).date()
			except:
				pass

			dists = pubTree.xpath('//*[@id="page-content"]/div[3]/div/div/div[2]/section/div/div[2]/h3/a')

			for element in dists:
				dist = Distribution(scraper)
				dist.title = element.text
				dist.downloadURL = urljoin("https://www.gov.scot", element.attrib['href'])
				dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
				if dist.mediaType in ACCEPTED_MIMETYPES:
					scraper.distributions.append(dist)
				else:
					pass

def scrape(scraper, tree):

	"""
	Scrapes GovScot landing page.
	When provided with a GovScot landing page this will determine whether it is a publication page - which contains
	the dataset(s) and metadata - or a collections page which contains links to many publications pages.
	If a publications link is provided it will take all the datasets on the publications page and turn them into
	distributions containing the dataURL and basic meta data. If a collections link is provided then it will open
	each publications link on the page and go through each adding to the list of distributions whenever an excel/csv
	file is found."""

	r = scraper.session.get(scraper.uri)
	if r.status_code != 200:
		raise Exception('Failed to get url {url}, with status code "{status_code}".'.format(url=url, status_code=r.status_code))

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

	logging.warning("This scraper has been depreciated. Please use the more recent version if viable")

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


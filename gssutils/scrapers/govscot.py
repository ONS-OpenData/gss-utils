import mimetypes
import re
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

from dateutil.parser import parse

from gssutils.metadata import GOV
from gssutils.metadata.dcat import Distribution


def scrape(scraper, tree):

	def pubs(soup):

		for a in soup.select('#page-content > div.top-matter > div > header > div:nth-child(1) > div > h1'):
			scraper.dataset.title = a.text

		for a in soup.select('#page-content > div.top-matter > div > header > div:nth-child(2) > div.grid__item.large--seven-twelfths > div > p'):
			scraper.dataset.description = a.text

		for a in soup.select('#page-content > div.inner-shadow-top.js-sticky-header-position.js-subpage-top-edge > div > div > div.grid__item.large--seven-twelfths > section'):
			a.xpath('div:nth-child(1) > div.document-info__text > h3 > a')

		try:
			pubDate = soup.findAll('span', class_= 'content-data__value')[0].text
			scraper.dataset.issued = pubDate
		except:
			pass

		dists = soup.findAll(class_= 'document-info')

		for entry in dists:
			distributions = entry.findAll(class_= 'no-icon')
			for i in distributions:
				dist = Distribution(scraper)
				dist.title = i.text
				dist.downloadURL = urljoin("https://www.gov.scot", i['href'])
				dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
				if dist.mediaType in ['application/msword', 'application/pdf', 'None']:
					return
				elif dist.mediaType == None:
					return
				else:
					scraper.distributions.append(dist)

	def colls(soup):

		pubPages = soup.findAll('ul', class_='collections-list')
		for page in pubPages:
			pages = page.findAll('a')
			for i in pages:
				req = Request(urljoin("https://www.gov.scot", i['href']), headers={'User-Agent': 'Mozilla/5.0'})
				html = urlopen(req).read()
				plaintext = html.decode('utf8')
				soup = BeautifulSoup(plaintext, 'html.parser')
				pubs(soup)

	r = scraper.session.get(scraper.uri)

	parse_object = urlparse(r.url)

	soup = BeautifulSoup(r.text, features="lxml")

	scraper.dataset.publisher = GOV['the-scottish-government']

	scraper.dataset.license = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'

	if 'publications' in parse_object.path:
		pubs(soup)
	elif 'collections' in parse_object.path:
		colls(soup)
	else:
		print('GovScot Scraper does not support given landing page')
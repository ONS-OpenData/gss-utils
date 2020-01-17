import mimetypes
import re
from datetime import datetime

from dateutil.parser import parse
import logging

from lxml import html

from gssutils.metadata import Distribution, ODS, ZIP, Excel, PDF, PMDDataset
from urllib.parse import urljoin, urlparse


def content_api(scraper, tree):
    final_url = False
    uri_components = urlparse(scraper.uri)
    content_api_path = uri_components.path
    while not final_url:
        metadata = scraper.session.get(f'https://www.gov.uk/api/content/{content_api_path}').json()
        schema = metadata['schema_name']
        if schema == 'redirect':
            if 'redirects' in metadata and len(metadata['redirects']) > 0:
                content_api_path = metadata['redirects'][0]['destination']
            else:
                logging.error('Content API response is a redirect, but no redirection found.')
        else:
            final_url = True
    if schema == 'document_collection':
        content_api_collection(scraper, metadata)
    elif schema == 'publication':
        scraper.dataset = content_api_publication(scraper, metadata)
        scraper.distributions = scraper.dataset.distribution
    elif schema == 'statistical_data_set':
        content_api_sds(scraper, metadata)
    else:
        logging.warning(f'Unknown schema type {schema}')


def content_api_collection(scraper, metadata):
    if 'title' in metadata:
        scraper.catalog.title = metadata['title']
    if 'description' in metadata:
        scraper.catalog.comment = metadata['description']
    if 'first_published_at' in metadata:
        scraper.catalog.issued = datetime.fromisoformat(metadata['first_published_at'])
    if 'public_updated_at' in metadata:
        scraper.catalog.modified = datetime.fromisoformat(metadata['public_updated_at'])
    if 'links' in metadata and 'organisations' in metadata['links']:
        orgs = metadata['links']['organisations']
        if len(orgs) == 0:
            logging.warning("No publishing organisations listed.")
        elif len(orgs) >= 1:
            if len(orgs) > 1:
                logging.warning('More than one organisation listed, taking the first.')
            scraper.catalog.publisher = orgs[0]["web_url"]
    scraper.catalog.dataset = []
    if 'links' in metadata and 'documents' in metadata['links']:
        for doc in metadata['links']['documents']:
            if 'schema_name' in doc and doc['schema_name'] == 'publication':
                ds = content_api_publication(scraper, doc)
                scraper.catalog.dataset.append(ds)


def content_api_publication(scraper, metadata):
    ds = PMDDataset()
    if 'title' in metadata:
        ds.title = metadata['title']
    if 'description' in metadata:
        ds.description = metadata['description']
    if 'api_url' in metadata:
        doc_info = scraper.session.get(metadata['api_url']).json()
    else:
        doc_info = metadata
    if 'first_published_at' in doc_info:
        ds.issued = datetime.fromisoformat(doc_info['first_published_at'])
    if 'public_updated_at' in doc_info:
        ds.modified = datetime.fromisoformat(doc_info['public_updated_at'])
    if 'links' in doc_info and 'organisations' in doc_info['links']:
        orgs = doc_info['links']['organisations']
        if len(orgs) == 0:
            logging.warning("No publishing organisations listed.")
        elif len(orgs) >= 1:
            if len(orgs) > 1:
                logging.warning('More than one organisation listed, taking the first.')
            ds.publisher = orgs[0]["web_url"]
    if 'details' in doc_info and 'documents' in doc_info['details']:
        distributions = []
        for link in doc_info['details']['documents']:
            link_tree = html.fromstring(link)
            div_attach = next(iter(link_tree.xpath("//div[@class='attachment-details']")), None)
            if div_attach is not None:
                div_metadata = next(iter(div_attach.xpath("p[@class='metadata']")), None)
                if div_metadata is not None:
                    span_type = next(iter(div_metadata.xpath("span[@class='type']")), None)
                    if span_type is not None:
                        span_size = next(iter(div_metadata.xpath("span[@class='file-size']/text()")), None)
                        if span_size is not None:
                            dist = Distribution(scraper)
                            # https://en.wikipedia.org/wiki/Kilobyte kB = 1000 while KB = 1024
                            # https://en.wikipedia.org/wiki/Megabyte MB = 10^6 bytes
                            if span_size.endswith('KB'):
                                dist.byteSize = int(float(span_size[:-2]) * 1024)
                            elif span_size.endswith('kB'):
                                dist.byteSize = int(float(span_size[:-2]) * 1000)
                            elif span_size.endswith('MB'):
                                dist.byteSize = int(float(span_size[:-2]) * 1000000)
                            anchor = next(iter(div_attach.xpath("h2/a")), None)
                            if anchor is not None:
                                url = anchor.get('href')
                                if url is not None:
                                    dist.downloadURL = urljoin('https://www.gov.uk/', url)
                                if hasattr(anchor, 'text'):
                                    dist.title = anchor.text.strip()
                            dist.mediaType, encoding = mimetypes.guess_type(dist.downloadURL)
                            abbr_type = next(iter(span_type.xpath("abbr/text()")), None)
                            if abbr_type is not None:
                                if abbr_type.upper() == 'PDF':
                                    dist.mediaType = PDF
                            distributions.append(dist)
        ds.distribution = distributions
    return ds


def content_api_sds(scraper, metadata):
    # publications are in the details/body HTML
    # they look to be a collection of datasets

    if 'description' in metadata:
        scraper.catalog.comment = metadata['description']
    if 'first_published_at' in metadata:
        scraper.catalog.issued = datetime.fromisoformat(metadata['first_published_at'])
    if 'public_updated_at' in metadata:
        scraper.catalog.modified = datetime.fromisoformat(metadata['public_updated_at'])
    if 'links' in metadata and 'organisations' in metadata['links']:
        orgs = metadata['links']['organisations']
        if len(orgs) == 0:
            logging.warning("No publishing organisations listed.")
        elif len(orgs) >= 1:
            if len(orgs) > 1:
                logging.warning('More than one organisation listed, taking the first.')
            scraper.catalog.publisher = orgs[0]["web_url"]
    scraper.catalog.dataset = []
    if 'details' in metadata and 'body' in metadata['details']:
        body_tree = html.fromstring(metadata['details']['body'])
        for heading in body_tree.xpath("//h2[following-sibling::p/descendant::span[@class='attachment-inline']]"):
            id = heading.get('id')
            ds = PMDDataset()
            ds.title = heading.text
            ds.comment = scraper.catalog.comment
            ds.publisher = scraper.catalog.publisher
            ds.issued = scraper.catalog.issued
            ds.modified = scraper.catalog.modified
            email_anchor = next(iter(body_tree.xpath("//a[@class='email']")), None)
            if email_anchor is not None:
                ds.contactPoint = email_anchor.get('href')
            ds.distribution = []
            for attachment in body_tree.xpath(f"//h2[@id='{id}']/" + \
                                              f"following-sibling::p[preceding-sibling::h2[1][@id='{id}']]/" + \
                                              "span[@class='attachment-inline']"):
                dist = Distribution(scraper)
                dist.title = next(iter(attachment.xpath("a/text()")), None)
                dist.downloadURL = next(iter(attachment.xpath("a/@href")), None)
                dist.mediaType, _ = mimetypes.guess_type(dist.downloadURL)
                abbr = next(iter(attachment.xpath("descendant::abbr/text()")), None)
                if abbr is not None:
                    if abbr.upper() == 'PDF':
                        dist.mediaType = PDF
                    elif abbr.upper() == 'ODS':
                        dist.mediaType = ODS
                size = next(iter(attachment.xpath("descendant::span[@class='file-size']/text()")), None)
                if size is not None:
                    if size.endswith('KB'):
                        dist.byteSize = int(float(size[:-2]) * 1024)
                    elif size.endswith('kB'):
                        dist.byteSize = int(float(size[:-2]) * 1000)
                    elif size.endswith('MB'):
                        dist.byteSize = int(float(size[:-2]) * 1000000)
                ds.distribution.append(dist)
            scraper.catalog.dataset.append(ds)

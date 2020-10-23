import json
import logging
import os
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import html2text
import msgpack
import requests
from cachecontrol import CacheControl, serialize
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import LastModified
from dateutil.parser import parse
from lxml import html
from rdflib import BNode, URIRef
from rdflib.graph import Dataset as RDFDataset

import gssutils.scrapers
from gssutils.metadata import namespaces, dcat, pmdcat, mimetype, GOV
from gssutils.utils import pathify, ensure_list


class BiggerSerializer(serialize.Serializer):

    def _loads_v4(self, request, data):
        try:
            cached = msgpack.loads(
                data, raw=False, max_bin_len=100 * 1000 * 1000)  # 100MB
        except ValueError:
            return

        return self.prepare_response(request, cached)


class FilterError(Exception):
    """ Raised when filters don't uniquely identify a thing
    """

    def __init__(self, message):
        self.message = message


class MetadataError(Exception):
    """ Raised when there is an issue with a provided metadata seed
    """

    def __init__(self, message):
        self.message = message


class Scraper:

    def __init__(self, uri: str = None, session: requests.Session = None, seed: str = None):

        # Airtable and gssutils are using slightly different field names....
        self.meta_field_mapping = {
            "published": "issued"
        }

        # Add an explicit on/off for temp scraping (based on presence of dataURL)
        self.temp_scrape = False

        # Use seed if provided
        if seed is not None:
            with open(seed, "r") as f:
                self.seed = json.load(f)
                if "dataURL" in self.seed:
                    logging.warning("A temporary dataURL has been specified; proceeding with a temp scrape.")
                    self.temp_scrape = True
                if "landingPage" not in self.seed.keys():
                    raise MetadataError('We always need to provide a "landingPage" via the seed. Either' \
                                    ' it\'s own or alongside a dataURL for temporary scrapes.')
                uri = self.seed["landingPage"]
        else:
            self.seed = None

        self.uri = uri
        self.dataset = pmdcat.Dataset(uri)
        self.catalog = dcat.Catalog()
        self.dataset.modified = datetime.now(timezone.utc).astimezone()
        self.distributions = []

        if session:
            self.session = session
        else:
            self.session = CacheControl(requests.Session(),
                                        cache=FileCache('.cache'),
                                        serializer=BiggerSerializer(),
                                        heuristic=LastModified())

        if 'JOB_NAME' in os.environ:
            self._base_uri = URIRef('http://gss-data.org.uk')
            self._dataset_id = pathify(os.environ['JOB_NAME'])
        else:
            self._base_uri = BNode()
            parsed_scrape_uri = urlparse(self.uri)
            self._dataset_id = parsed_scrape_uri.netloc.replace('.', '/') + parsed_scrape_uri.path
        self.update_dataset_uris()
        self._run()

    def _repr_markdown_(self):
        md = ""
        if hasattr(self.catalog, 'dataset') and len(self.catalog.dataset) > 1 and len(self.distributions) == 0:
            md = md + f'## {self.catalog.title}\n\nThis is a catalog of datasets; choose one from the following:\n\n'
            md = md + '\n'.join([f'* {d.label}' for d in self.catalog.dataset])
        else:
            if hasattr(self.dataset, 'label'):
                md = md + f'## {self.dataset.label}\n\n'
            if hasattr(self.dataset, 'comment'):
                md = md + f'{self.dataset.comment}\n\n'
            if hasattr(self.dataset, 'description'):
                md = md + f'### Description\n\n{self.dataset.description}\n\n'
            if len(self.distributions) > 0:
                md = md + "### Distributions\n\n"
                for d in self.distributions:
                    t = {mimetype.Excel: 'MS Excel Spreadsheet', mimetype.ODS: 'ODF Spreadsheet'}
                    if hasattr(d, 'issued'):
                        md = md + f"1. {d.title} ([{t.get(d.mediaType, d.mediaType)}]({d.downloadURL})) - {d.issued}\n"
                    else:
                        md = md + f"1. {d.title} ([{t.get(d.mediaType, d.mediaType)}]({d.downloadURL}))\n"

        return md

    @staticmethod
    def to_markdown(node):
        if type(node) == list:
            return html2text.html2text('\n'.join([html.tostring(n, encoding='unicode') for n in node]))
        else:
            return html2text.html2text(html.tostring(node, encoding='unicode'))

    def _run(self):
        scraped = False

        # Using a temporary scraper
        if self.temp_scrape:
            temp_uri = self.seed["dataURL"]
            page = self.session.get(temp_uri)
            scraped = self._attempt_scraper_from_seed()
            
        # Using a standard scraper
        else:
            page = self.session.get(self.uri)
            # TODO - not all scrapers will necessarily need the beautified HTML DOM
            tree = html.fromstring(page.text)
            
            # Look for a scraper based on the uri
            for start_uri, scrape in gssutils.scrapers.scraper_list:
                if self.uri.startswith(start_uri):

                    # Scrape
                    scrape(self, tree)
                    scraped = True

                    # If we have a seed..
                    if self.seed is not None:
                        self._populate_missing_metadata()  # Plug any metadata gaps
                    break

        if not scraped:
            raise NotImplementedError(f'No scraper for {self.uri} and insufficient seed metadata passed.')

        # Apply overrides to either method of scraping
        if self.seed is not None:
            self._override_metadata_where_specified()

        return self

    def _populate_missing_metadata(self):
        """
        Use the seed file to populate any missing metadata fields.
        """

        try:
            # Dataset level metadata
            if not hasattr(self.dataset, 'title') and "title" in self.seed.keys():
                self.dataset.title = self.seed["title"]
            if not hasattr(self.dataset, 'description') and "description" in self.seed.keys():
                self.dataset.description = self.seed["description"]
            if not hasattr(self.dataset, 'publisher') and "publisher" in self.seed.keys():
                self.dataset.publisher = GOV[pathify(self.seed["publisher"])]
            if not hasattr(self.dataset, 'family') and "families" in self.seed.keys():
                self.dataset.family = pathify(self.seed["families"][0])
                
        except Exception as e:
            raise MetadataError("Aborting. Issue encountered while attempting checking "
                                "the info.json for supplementary metadata.") from e

        # Populate missing distribution level Metadata
        for distribution in self.distributions:

            # NOTE - Don't EVER add a fallback for downloadURL or issued here!! this is a specific safety
            # to stop us "temporary scraping" and publishing new data with old metadata
            if hasattr(distribution, 'downloadURL') and not hasattr(distribution, 'mediaType'):
                if distribution.downloadURL.lower().endswith(".xls"):
                    distribution.mediaType = mimetype.Excel
                elif distribution.downloadURL.lower().endswith(".xlsx"):
                    distribution.mediaType = mimetype.ExcelOpenXML
                elif distribution.downloadURL.lower().endswith(".ods"):
                    distribution.mediaType = mimetype.ODS
                elif distribution.downloadURL.lower().endswith(".csv"):
                    distribution.mediaType = mimetype.CSV
                elif distribution.downloadURL.lower().endswith(".zip"):
                    distribution.mediaType = mimetype.ZIP
                else:
                    logging.warning("Unable to find mediaType for distribution")
                

    def _override_metadata_where_specified(self):
        """
        Where metadata is supplied by both the seed and the scraper, override to the values
        in the seed - ONLY where the field in question appears under the overrides key
        """

        # fields we should not be overridingm because it can lead to new data with old metadata
        disallowed = [
            "issued",
            "downloadURL"
        ]

        if "overrides" not in self.seed.keys():
            return  # moot point
        else:
            for field in self.seed["overrides"]:

                # Airtable and gssutils are using slightly different field names....
                if field in self.meta_field_mapping:
                    target_field = self.meta_field_mapping[field]
                else:
                    target_field = field

                if target_field in disallowed:
                    raise MetadataError("Aborting, you cannot override the '{}' field.".format(target_field))

                if not hasattr(self.dataset, target_field):
                    raise MetadataError("Aborting. We've specified an override to the '{}' field"
                                        "but the dataset does not have that attribute.".format(field))
                self.dataset.__setattr__(target_field, self.seed[field])
                self._propagate_metadata_to_distributions(target_field, self.seed[field])

    def _propagate_metadata_to_distributions(self, target_field, value):
        """
        As it says, if we're updating a metadata field update it for all distributions
        """

        # If it's a catalogue we'll need to account for one more level
        if isinstance(self, dcat.Catalog):
            try:
                for distro in self.dataset.distributions:
                    if hasattr(distro, target_field):
                        distro.__setattr__(target_field, value)
            except Exception as e:
                raise MetadataError("Aborting. Encountered issue propagating overritten metadata to"
                                    " distributions within then dataset within the catalogue.") from e
        else:
            try:
                for distro in self.distributions:
                    if hasattr(distro, target_field):
                        distro.__setattr__(target_field, value)
            except Exception as e:
                raise MetadataError("Aborting. Encountered issue propagating overritten metadata to"
                                    " distributions within the dataset.") from e

    def _attempt_scraper_from_seed(self):
        """
        Validates then creates a simple scraper from the metadata in the seed.
        """

        # Make sure we have the 100% required stuff
        keys = ["title", "description", "dataURL", "publisher", "published", "families"]
        not_found = []
        for key in keys:
            if key not in self.seed.keys():
                if self.seed[key] is not None:
                    not_found.append(key)

        if len(not_found) > 0:
            raise NotImplementedError(
                f'A "temporary scape" is not possible as the following required ' 
                f'fields were missing from the seed metadata: {",".join(not_found)}. got: {",".join(self.seed.keys())}.'
            )

        # Populate the "unsafe" fields explicitly, then populate the missing
        # metadata from the seed
        dist = dcat.Distribution(self)
        dist.issued = parse(self.seed["published"]).date()
        dist.downloadURL = self.seed["dataURL"]
        self.family = pathify(self.seed["families"][0])
        self.distributions.append(dist)
        self.dataset.issued = dist.issued
        self._populate_missing_metadata()

        # Sanity check - break if our download doesn't point to a specific instance of a file
        allowed = ["xls", "xlsx", "ods", "zip", "csv"]
        if dist.downloadURL.lower().split(".")[-1] not in allowed:
            raise MetadataError("A temporary scraper must point to a specific data file resouce. "
                                "Download url is {} but must end with one of: {}"
                                .format(dist.downloadURL, ",".join(allowed)))
        return True

    @staticmethod
    def _filter_one(things, **kwargs):
        latest = kwargs.pop('latest', False)
        matches = [
            d for d in things if all(
                [v(d.__dict__[k]) if callable(v) else (hasattr(d, k) and d.__dict__[k] == v)
                 for k, v in kwargs.items()]
            )]
        if len(matches) > 1:
            if latest:
                return max(matches, key=lambda d: d.issued)
            else:
                raise FilterError('more than one match for given filter(s)')
        elif len(matches) == 0:
            raise FilterError('nothing matches given filter(s)')
        else:
            return matches[0]

    def select_dataset(self, **kwargs):
        dataset = self._filter_one(self.catalog.dataset, **kwargs)
        self.dataset = dataset
        self.dataset.landingPage = self.uri
        if not hasattr(self.dataset, 'description') and hasattr(self.catalog, 'description'):
            self.dataset.description = self.catalog.description
        self.dataset.modified = datetime.now()  # TODO: decision on modified date
        self.update_dataset_uris()
        self.distributions = dataset.distribution

    def distribution(self, **kwargs):
        return self._filter_one(self.distributions, **kwargs)

    def set_base_uri(self, uri):
        self._base_uri = uri
        self.update_dataset_uris()

    def set_dataset_id(self, id):
        self._dataset_id = id
        self.update_dataset_uris()

    def update_dataset_uris(self):
        self.dataset.uri = urljoin(self._base_uri, f'data/{self._dataset_id}-catalog-entry')
        self.dataset.set_graph(urljoin(self._base_uri, f'graph/{self._dataset_id}-metadata'))

    def set_family(self, family):
        self.dataset.family = family

    def set_theme(self, theme):
        self.dataset.theme = theme

    def set_description(self, description):
        self.dataset.description = description

    def as_quads(self, catalog_id=None):
        catalog = dcat.Catalog()
        if catalog_id is not None:
            catalog.uri = urljoin(self._base_uri, catalog_id)
        else:
            catalog.uri = urljoin(self._base_uri, 'catalog/datasets')
        metadata_graph = urljoin(self._base_uri, f'graph/{self._dataset_id}-metadata')
        catalog.set_graph(metadata_graph)
        catalog.record = pmdcat.CatalogRecord()
        catalog.record.uri = urljoin(self._base_uri, f'data/{self._dataset_id}-catalog-record')
        catalog.record.set_graph(metadata_graph)
        catalog.record.label = self.dataset.label + " Catalog Record"
        catalog.record.metadataGraph = metadata_graph
        catalog.record.issued = self.dataset.issued
        catalog.record.modified = self.dataset.modified
        catalog.record.primaryTopic = self.dataset
        # need to ensure that all the pointed to things are in the same graph
        if hasattr(catalog.record.primaryTopic, 'distribution'):
            for dist in ensure_list(catalog.record.primaryTopic.distribution):
                dist.set_graph(metadata_graph)
        self.dataset.graph = urljoin(self._base_uri, f'graph/{self._dataset_id}')
        self.dataset.datasetContents = pmdcat.DataCube()
        self.dataset.datasetContents.uri = urljoin(self._base_uri, f'data/{self._dataset_id}#dataset')
        self.dataset.sparqlEndpoint = urljoin(self._base_uri, '/sparql')
        quads = RDFDataset()
        quads.namespace_manager = namespaces
        catalog.add_to_dataset(quads)
        return quads

    def generate_trig(self, catalog_id=None):
        return self.as_quads(catalog_id).serialize(format='trig')

    @property
    def title(self):
        return self.dataset.title

    @property
    def description(self):
        return self.dataset.description

    @property
    def publication_date(self):
        return self.dataset.issued.isoformat()

    @property
    def next_release(self):
        return self.dataset.updateDueOn.isoformat()

    @property
    def contact(self):
        return self.dataset.contactPoint

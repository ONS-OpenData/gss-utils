import json
import logging
import os
import copy

from pathlib import Path
from urllib.parse import urljoin
from typing import Optional

from gssutils.csvw.mapping import CSVWMapping
from gssutils.utils import pathify


class Cubes:
    """
    A class representing multiple datacubes
    """

    def __init__(self, info_json="info.json", destination_path="out", base_uri="http://gss-data.org.uk",
                 job_name=None):

        with open(info_json, "r") as info_file:
            self.info = json.load(info_file)

        # Where we don't have a mapping field, add one to avoid iteration errors later
        if "columns" not in self.info["transform"].keys():
            self.info["transform"]["columns"] = {}

        self.destination_folder = Path(destination_path)
        self.destination_folder.mkdir(exist_ok=True, parents=True)
        self.base_uri = base_uri
        self.cubes = []
        self.has_ran = False
        
        if job_name is not None:
            logging.warning("The passing of job_name= has been depreciated and no longer does anything, please"
                            "remove this keyword argument")

    def add_cube(self, scraper, dataframe, title, graph=None, info_json_dict=None, override_containing_graph=None):
        """
        Add a single datacube to the cubes class.
        """
        self.cubes.append(Cube(self.base_uri, scraper, dataframe, title, graph, info_json_dict,
                               override_containing_graph))

    def output_all(self):
        """
        Output every cube object we've added to the cubes() class.
        """

        if len(self.cubes) == 0:
            raise Exception("Please add at least one datacube with '.add_cube' before "
                            "calling output_all().")

        # Don't let people add 1, output 1, add 2 output 2 etc
        # They'll want to but it'll mangle the url namespacing
        if self.has_ran:
            raise Exception("Calling 'output_all' on the Cubes class is a destructive process and "
                            "has already run. You need to (re)add all your datacubes before doing so.")

        # Are we outputting more than one cube? We need to know this before we output
        is_multi_cube = len(self.cubes) >= 2

        # The many-to-one scenario
        # If all cubes are getting written to a single graph it plays hell with the
        # single vs multiple namespaces logic, so we're going to explicitly check for and handle that
        is_many_to_one = False
        if is_multi_cube:
            to_graph_statements = [x.graph for x in self.cubes if x.graph is not None]
            if len(to_graph_statements) == len(self.cubes):
                if len(set(to_graph_statements)) == 1:
                    is_many_to_one = True

        for cube in self.cubes:
            try:
                cube.output(self.destination_folder, is_multi_cube, is_many_to_one, self.info)
            except Exception as err:
                raise Exception("Exception encountered while processing datacube '{}'." \
                                .format(cube.title)) from err
        self.has_ran = True


class Cube:
    """
    A class to encapsulate the dataframe and associated metadata that constitutes a single datacube
    """
    override_containing_graph_uri: Optional[str]

    def __init__(self, base_uri, scraper, dataframe, title, graph, info_json_dict,
                 override_containing_graph_uri: Optional[str]):

        self.scraper = scraper  # note - the metadata of a scrape, not the actual data source
        self.dataframe = dataframe
        self.title = title
        self.scraper.set_base_uri(base_uri)
        self.graph = graph
        self.info_json_dict = copy.deepcopy(info_json_dict)  # don't copy a pointer, snapshot a thing
        self.override_containing_graph_uri = override_containing_graph_uri

    def _instantiate_map(self, destination_folder, pathified_title, info_json):
        """
        Create a basic CSVWMapping object for this cube
        """
        map_obj = CSVWMapping()

        # Use the info.json for the mapping by default, but let people
        # pass a new one in (for where we need to get clever)
        info_json = info_json if self.info_json_dict is None else self.info_json_dict

        map_obj.set_accretive_upload(info_json)
        map_obj.set_mapping(info_json)

        map_obj.set_csv(destination_folder / f'{pathified_title}.csv')
        map_obj.set_dataset_uri(urljoin(self.scraper._base_uri, f'data/{self.scraper._dataset_id}'))

        if self.override_containing_graph_uri:
            map_obj.set_containing_graph_uri(self.override_containing_graph_uri)
        else:
            map_obj.set_containing_graph_uri(self.scraper.dataset.pmdcatGraph)

        return map_obj

    def _populate_csvw_mapping(self, destination_folder, pathified_title,
                               info_json):
        """
        Use the provided details object to generate then fully populate the mapping class
        """

        # The base CSVWMapping class
        map_obj = self._instantiate_map(destination_folder, pathified_title, info_json)

        # TODO - IF we do codelist generation here, this would be the point of intervention

        return map_obj

    def output(self, destination_folder, is_multi_cube, is_many_to_one, info_json):
        """
        Outputs the csv and csv-w schema for a single 'Cube' held in the 'Cubes' object
        """
        graph_name = pathify(self.title) if self.graph is None else pathify(self.graph)
        if isinstance(self.scraper.dataset.family, list):
            primary_family = pathify(self.scraper.dataset.family[0])
        else:
            primary_family = pathify(self.scraper.dataset.family)

        main_dataset_id = info_json.get('id', Path.cwd().name)
        if is_many_to_one:
            # Sanity check, because this isn't an obvious as I'd like / a bit weird
            err_msg = 'Aborting. Where you are writing multiple cubes to a single output graph, the ' \
                      + 'pathified graph specified needs to match you pathified current working directory. ' \
                      + 'Got "{}", expected "{}".'.format(graph_name, pathify(Path(os.getcwd()).name))
            assert main_dataset_id == graph_name, err_msg

            logging.warning("Output Scenario 1: Many cubes written to the default output (cwd())")
            dataset_path = f'gss_data/{primary_family}/{graph_name}'
        elif is_multi_cube:
            logging.warning("Output Scenario 2: Many cubes written to many stated outputs")
            dataset_path = f'gss_data/{primary_family}/{main_dataset_id}/{graph_name}'
        else:
            logging.warning("Output Scenario 3: A single cube written to the default output (cwd())")
            dataset_path = f'gss_data/{primary_family}/{main_dataset_id}'
        self.scraper.set_dataset_id(dataset_path)

        # output the tidy data
        self.dataframe.to_csv(destination_folder / f'{pathify(self.title)}.csv', index=False)

        is_accretive_upload = info_json is not None and "load" in info_json and "accretiveUpload" in info_json["load"] \
                              and info_json["load"]["accretiveUpload"]

        # Don't output trig file if we're performing an accretive upload.
        # We don't want to duplicate information we already have.
        if not is_accretive_upload:
            # Output the trig
            trig_to_use = self.scraper.generate_trig()
            with open(destination_folder / f'{pathify(self.title)}.csv-metadata.trig', 'wb') as metadata:
                metadata.write(trig_to_use)

        # Output csv and csvw
        populated_map_obj = self._populate_csvw_mapping(destination_folder, pathify(self.title), info_json)
        populated_map_obj.write(destination_folder / f'{pathify(self.title)}.csv-metadata.json')

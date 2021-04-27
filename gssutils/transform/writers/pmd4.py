import os
import logging
from pathlib import Path
from urllib.parse import urljoin

from gssutils.csvw.mapping import CSVWMapping
from gssutils.transform.writers.abstract import CubeWriter
from gssutils import pathify

class PMD4Writer(CubeWriter):
    """
    An implementation of the CubeWriter abstract (i.e a "driver") that outputs data
    and metadata to satisfy the PMD4 platform
    """

    @staticmethod
    def get_out_path():
        """
        Returns the output directory of the driver
        """
        return Path("out")

    def check_inputs(self):
        """
        Confirm that the driver has been passed the required args
        and kwargs
        """

        # Note: you could arguably have this inside Cubes() but I'm not convinced
        # the arguments to each writer should be the same. They are _for now_ but
        # that seems like a thing that could/should change in the longer term.
        is_multi_cube = self.args[0]
        is_many_to_one = self.args[1]
        info_json = self.args[2]

        assert isinstance(is_multi_cube, bool), ('arg is_multi_cube should be'
            f' of type "bool", got {type(is_multi_cube)}.')
        self.is_multi_cube: bool = is_multi_cube

        assert isinstance(is_many_to_one, bool), ('arg is_many_to_one should be'  
            f' of type "bool", got {type(is_many_to_one)}.')
        self.is_many_to_one: bool = is_many_to_one

        assert isinstance(info_json, dict), ('arg info_json should be'  
            f' of type "dict", got {type(info_json)}.')
        # Where we don't have a mapping field, add one to avoid iteration errors later
        if "columns" not in info_json["transform"]:
            info_json["transform"]["columns"] = {}
        self.info_json: dict = info_json

        self.destination_folder: Path = self.get_out_path()
        
    def format_data(self):
        """
        Where modifications to the underlying dataframe are required,
        they happen here
        """
        # TODO - somehow
        pass

    def validate_data(self):
        """
        Where you validate the datacube
        """
        # TODO - somehow
        pass

    def output_data(self):
        """
        Output the encapsulated dataframe to the required format and
        to the required place
        """
        self.cube.dataframe.to_csv(self.destination_folder / f'{pathify(self.cube.title)}.csv', index=False)

    def format_metadata(self):
        """
        Where modifications to the underlying metadata are required,
        they happen here
        """
        graph_name = pathify(self.cube.title) if self.cube.graph is None else pathify(self.cube.graph)
        if isinstance(self.cube.scraper.dataset.family, list):
            primary_family = pathify(self.cube.scraper.dataset.family[0])
        else:
            primary_family = pathify(self.cube.scraper.dataset.family)

        main_dataset_id = self.info_json.get('id', Path.cwd().name)
        if self.is_many_to_one:
            # Sanity check, because this isn't an obvious as I'd like / a bit weird
            err_msg = 'Aborting. Where you are writing multiple cubes to a single output graph, the ' \
                      + 'pathified graph specified needs to match you pathified current working directory. ' \
                      + 'Got "{}", expected "{}".'.format(graph_name, pathify(Path(os.getcwd()).name))
            assert main_dataset_id == graph_name, err_msg

            logging.info("Output Scenario 1: Many cubes written to the default output (cwd())")
            dataset_path = f'gss_data/{primary_family}/{graph_name}'
        elif self.is_multi_cube:
            logging.info("Output Scenario 2: Many cubes written to many stated outputs")
            dataset_path = f'gss_data/{primary_family}/{main_dataset_id}/{graph_name}'
        else:
            logging.info("Output Scenario 3: A single cube written to the default output (cwd())")
            dataset_path = f'gss_data/{primary_family}/{main_dataset_id}'
        self.cube.scraper.set_dataset_id(dataset_path)

    def validate_metadata(self):
        """
        Where you validate the metadata
        """
        # TODO - somehow
        pass

    def output_metadata(self):
        """
        Output the encapsulated metadata to the required format and
        to the required place
        """

        # True, if all the statements are
        is_accretive_upload = all([
            not self.info_json,
            "load" in self.info_json,
            "accretiveUpload" in self.info_json["load"],
            self.info_json["load"]["accretiveUpload"]
        ])

        # Don't output trig file if we're performing an accretive upload.
        # We don't want to duplicate information we already have.
        if not is_accretive_upload:
            # Output the trig
            trig_to_use = self.cube.scraper.generate_trig()
            with open(self.destination_folder / f'{pathify(self.cube.title)}.csv-metadata.trig', 'wb') as metadata:
                metadata.write(trig_to_use)

        # Output csv and csvw
        populated_map_obj = self._populate_csvw_mapping(self.destination_folder, pathify(self.cube.title), self.info_json)
        populated_map_obj.write(self.destination_folder / f'{pathify(self.cube.title)}.csv-metadata.json')


    # Dev note:
    # From this point are private methods specific to this implementation of the CubeWriter driver,
    # it would be nice to keep this convention going.

    def _instantiate_map(self, destination_folder, pathified_title, info_json):
        """
        Create a basic CSVWMapping object for this cube
        """
        map_obj = CSVWMapping()

        # Use the info.json for the mapping by default, but let people
        # pass a new one in (for where we need to get clever)
        info_json = info_json if self.cube.info_json_dict is None else self.cube.info_json_dict

        map_obj.set_accretive_upload(info_json)
        map_obj.set_mapping(info_json)

        map_obj.set_csv(destination_folder / f'{pathified_title}.csv')
        map_obj.set_dataset_uri(urljoin(self.cube.scraper._base_uri, f'data/{self.cube.scraper._dataset_id}'))

        if self.cube.override_containing_graph_uri:
            map_obj.set_containing_graph_uri(self.cube.override_containing_graph_uri)
        else:
            map_obj.set_containing_graph_uri(self.cube.scraper.dataset.pmdcatGraph)

        return map_obj

    def _populate_csvw_mapping(self, destination_folder, pathified_title,
                               info_json):
        """
        Use the provided details object to generate then fully populate the mapping class
        """

        # The base CSVWMapping class
        map_obj = self.cube._instantiate_map(destination_folder, pathified_title, info_json)

        # TODO - IF we do codelist generation here, this would be the point of intervention

        return map_obj       
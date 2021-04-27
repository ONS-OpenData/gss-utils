import json
from pathlib import Path

from gssutils.transform.writers.abstract import CubeWriter

class CMDWriter(CubeWriter):
    """
    An implementation of the CubeWriter abstract (i.e a "driver") that outputs data
    and metadata to satisfy the CMD platform
    """

    @staticmethod
    def get_out_path():
        """
        Returns the output directory of the driver
        """
        return Path("cmd-out")

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
        pass

    def validate_data(self):
        """
        Where you validate the datacube
        """
        pass

    def output_data(self):
        """
        Output the encapsulated dataframe to the required format and
        to the required place
        """
        pass

    def format_metadata(self):
        """
        Where modifications to the underlying metadata are required,
        they happen here
        """
        
        # Currently unsure what CMD needs so (for now) we're gonna dump a simple json dict
        # alongside the csv

        with open(f'{self.destination_folder}/metadata.json', 'w') as f:
            json.dump({
                "title": self.cube.scraper.title,
                "description": self.cube.scraper.description
            }, f, indent=2)

    def validate_metadata(self):
        """
        Where you validate the metadata
        """
        pass

    def output_metadata(self):
        """
        Output the encapsulated metadata to the required format and
        to the required place
        """
        pass
import logging
import json
from pathlib import Path

import pandas as pd

from gssutils.transform.writers.abstract import CubeWriter
from gssutils import pathify

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

        if info_json:
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
        they happen here. These changed occur to ALL dataframes
        written by this CubeWriter.

        You're modifying self.cube.dataframe
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
        column_map = self.info_json["transform"]["columns"]

        assert "Value" in column_map, (f'To create a CMD v4 output you need to have specified'
                ' a "Value" column via your column mapping.')

        marker_column = [x for x in self.cube.dataframe if x in ["Markers", "Marker"]]
        attribute_columns = {k:v for (k, v) in column_map.items() if "attribute" in v}

        for unwanted_col in attribute_columns:
            column_map.pop(unwanted_col)
        column_map.pop("Value")

        assert "Value" in self.cube.dataframe, (f'Column map is specifying a "Value" column '
                f'but one does not exist in your dataframe, got {self.cube.dataframe.values}')

        additional_column_count = len(marker_column) + len(attribute_columns)
        v4_col = f'V4_{additional_column_count}'

        new_columns = list(attribute_columns.keys()) + list(column_map.keys())

        # TODO - change it in place, this will eat memory as-is
        df = pd.DataFrame()
        df[v4_col] = self.cube.dataframe["Value"]
        for col in new_columns:
            df[col] = self.cube.dataframe[col]

        df.to_csv(self.destination_folder / f'{pathify(self.cube.title)}.csv', index=False)

    def format_metadata(self):
        """
        Where modifications to the underlying metadata are required,
        they happen here
        """

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
        # Currently unsure what CMD needs so (for now) we're gonna dump a simple json dict
        # alongside the csv

        with open(f'{self.destination_folder}/metadata.json', 'w') as f:
            json.dump({
                "title": self.cube.scraper.title,
                "description": self.cube.scraper.description
            }, f, indent=2)
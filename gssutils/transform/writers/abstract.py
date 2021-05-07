
from abc import ABCMeta, abstractmethod
from copy import deepcopy
import logging

import pandas as pd

class PostProccessingError(Exception):
    """
    Occurs when an exception is throw when applying post processing/formatting to a 
    thing (usually but not exclusively a dataframe) containing the data of the datacube
    and/or datacube slice
    """
    def __init__(self, msg):
        self.msg = msg


class CubeWriter(metaclass=ABCMeta):
    """
    An abstract encapsulating the requirements of a driver and functions in common
    for outputting a datacube and its metadata
    """

    def __init__(self, *args, cube = None, formaters: list = [], **kwargs):

        assert cube, ('Every "CubeWriter" driver must be passed something that '
            'represents a cube of data via the cube= keyword argument')

        # Note: taking copies as otherwise we're pointing back the the SAME variable
        # with every writer, hair pulling madness ensues
        self.cube = deepcopy(cube)
        self.args: list = deepcopy(args)
        self.kwargs: dict = deepcopy(kwargs)
        self.formaters: list = deepcopy(formaters)

        # The order we do things.
        # Shouldn't change, but lets set it up so it can
        self.operational_sequence = (
            self.check_inputs,
            self.format_metadata,
            self.validate_metadata,
            self.format_data,
            self.dynamic_format_data,
            self.validate_data,
            self.output_data,
            self.output_metadata,
            self._cleanup
            )

    def _cleanup(self):
        """
        Given we need a per-writer copy of everything, clean up after each
        write to mimimise the footprint
        """
        self.cube = None
        self.args = None
        self.kwargs = None
        self.formatters = None

    def dynamic_format_data(self):
        """
        Where dataframe modifying functions are passed into the CubeWriter
        they happen here.
        """
        for post_processer in self.formaters:
            logging.warning(f'Applying {post_processer} to {self}')
            try:
                self.cube.dataframe = post_processer(self.cube.dataframe)
            except Exception as err:
                raise PostProccessingError(f'When using {self} and {post_processer}') from err

    @staticmethod
    @abstractmethod
    def get_out_path():
        """
        Returns the output directory of the driver

        Note: staticmethod so we can call this before instantiation
        and raise early for incorrect configuration
        """
        pass

    @abstractmethod
    def check_inputs(self):
        """
        Confirm that the driver has been passed the required args
        and kwargs
        """
        pass

    @abstractmethod
    def format_data(self):
        """
        Where modifications to the underlying dataframe are required,
        they happen here. These changed occur to ALL dataframes
        written by this CubeWriter.

        You're modifying self.cube.dataframe
        """
        pass   

    @abstractmethod
    def validate_data(self):
        """
        Where you validate the datacube
        """
        pass

    @abstractmethod
    def output_data(self):
        """
        Output the encapsulated dataframe to the required format and
        to the required place
        """
        pass

    @abstractmethod
    def format_metadata(self):
        """
        Where modifications to the underlying metadata are required,
        they happen here
        """
        pass

    @abstractmethod
    def validate_metadata(self):
        """
        Where you validate the metadata
        """
        pass

    @abstractmethod
    def output_metadata(self):
        """
        Output the encapsulated metadata to the required format and
        to the required place
        """
        pass
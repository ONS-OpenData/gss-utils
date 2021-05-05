from abc import ABCMeta, abstractmethod
import pandas as pd

class CubeWriter(metaclass=ABCMeta):
    """
    An abstract encapsulating the requirements of a driver that outputs
    a datacube and its metadata
    """

    def __init__(self, *args, cube = None, formatters = [], **kwargs):

        assert cube, ('Every writer must be passed a Cube object, via '
                'the cube keyword argument')

        # TODO - assert the types of everything match
        self.cube = cube
        self.args: list = args
        self.kwargs: dict = kwargs
        self.formatters: list = formatters

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
            )

    def dynamic_format_data(self):
        """
        Where dataframe modifying functions are passed into the CubeWriter
        they happen here.
        """
        for post_processer in self.formatters:
            self.cube.dataframe = post_processer(self.cube.dataframe)

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
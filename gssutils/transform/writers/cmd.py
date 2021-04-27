
from gssutils.transform.writers.abstract import CubeWriter

class CMDWriter(CubeWriter):
    """
    An implementation of the CubeWriter abstract (i.e a "driver") that outputs data
    and metadata to satisfy the CMD platform
    """

    def check_inputs(self):
        """
        Confirm that the driver has been passed the required args
        and kwargs
        """
        pass

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
        pass

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
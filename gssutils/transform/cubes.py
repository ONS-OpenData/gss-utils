import json
import logging
import copy

from pathlib import Path
from typing import Optional

from gssutils.transform.writers import PMD4Writer

class Cubes:
    """
    A class representing multiple datacubes
    """

    def __init__(self, info_json="info.json", destination_path="out", base_uri="http://gss-data.org.uk",
                 job_name=None, writers=PMD4Writer):

        with open(info_json, "r") as info_file:
            self.info = json.load(info_file)

        # Where we don't have a mapping field, add one to avoid iteration errors later
        if "columns" not in self.info["transform"].keys():
            self.info["transform"]["columns"] = {}

        self.writers = writers
        self.destination_folder = Path(destination_path)
        self.destination_folder.mkdir(exist_ok=True, parents=True)
        self.base_uri = base_uri
        self.cubes = []
        self.has_ran = False
        
        if job_name is not None:
            logging.warning("The passing of job_name= has been depreciated and no longer does anything, please"
                            "remove this keyword argument")

    def add_cube(self, scraper, dataframe, title, graph=None, info_json_dict=None, override_containing_graph=None,
            writer_override = None):
        """
        Add a single datacube to the cubes class.
        """
        self.cubes.append(Cube(self.base_uri, scraper, dataframe, title, graph, info_json_dict,
                               override_containing_graph, writer_override))

    def output_all(self, raise_writer_exceptions: bool = False):
        """
        Output every cube object we've added to the cubes() class.

        raise_writer_exceptions: lets us flag off gracefully handling output errors per-driver
        (because we do want things to fail loudly while testing)
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

        # NOTE - this whole bit of pre-output logic is very coupled to pmd and graphs,
        # ideally we want to get rid of it 

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
                cube.output(self.destination_folder, is_multi_cube, is_many_to_one, self.info,
                        self.writers, raise_writer_exceptions)
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
                 override_containing_graph_uri: Optional[str], writer_override):

        self.scraper = copy.deepcopy(scraper)  # note - the metadata of a scrape, not the actual data source
        self.dataframe = dataframe
        self.title = title
        self.scraper.set_base_uri(base_uri)
        self.graph = graph
        self.info_json_dict = copy.deepcopy(info_json_dict)  # don't copy a pointer, snapshot a thing
        self.override_containing_graph_uri = override_containing_graph_uri

        # I'm not 100% but it's conceivable that we'll want to output a subset of the
        # defined cubes to different places, so we're including a per-cube writer override
        # as a precaution against that eventuality.
        self.writer_override = writer_override


    def output(self, destination_folder, is_multi_cube, is_many_to_one, info_json, writers, raise_writer_exceptions):
        """
        Outputs the required per-platform inputs for a single 'Cube' held in the 'Cubes' object
        """

        # DE knows best
        if self.writer_override:
            writers = self.writer_override

        # Force writer iterable, so we can support outputting a cube with more than one
        writers = [writers] if not isinstance(writers, list) and not isinstance(writers, tuple) else writers
        
        for writer in writers:

            # We're going to catch this, as one writer output failing shouldn't stop us trying the next
            # note - flagged off while testing, see "raise_writer_exceptions" coming from Cubes.output_all()
            try:
                this_writer = writer(destination_folder, is_multi_cube, is_many_to_one, info_json, cube=self)

                 # TODO - can wrap this whole loop fairly trivially, but undecided on points of intervention, decide
                for operation in this_writer.operational_sequence:
                    operation()
            
            except Exception as err:
                logging.warning(f'Output failed for writer {type(writer)} with exception:\n {err}') 
                if raise_writer_exceptions:
                    raise err
   



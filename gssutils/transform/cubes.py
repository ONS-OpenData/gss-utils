from gssutils.transform.download import FormatError
import json
import logging
import copy

from pathlib import Path
from typing import Optional, List

from gssutils.transform.writers import PMD4Writer, CMDWriter, CubeWriter

STANDARD_FORMATTERS = {"PMD4": PMD4Writer, "CMD": CMDWriter}

class Cubes:
    """
    A class representing multiple datacubes
    """

    def __init__(self, info_json="info.json", destination_path="out", base_uri="http://gss-data.org.uk",
                 job_name=None, writers=PMD4Writer, formatters=None):

        # I don't _think_ we're using the destination_path keyword anywhere (and it's irrelevant with the
        # introduction of CubeWriter) but we'll run a depreciation warning for a few months rather than 
        # straight remove it as a precaution -27/4/2021- 
        if destination_path != "out":
            logging.warning(f'The Cubes(destination_path=) keyword is being depreciated. Please remove '
                    'it from your transform')

        with open(info_json, "r") as info_file:
            self.info = json.load(info_file)
            
        # Force writer iterable, so we can support outputting a cube with more than one
        # without making users pass in lists of 1
        writers = [writers] if not isinstance(writers, list) and not isinstance(writers, tuple) else writers
        self.writers: List[CubeWriter] = writers

        # Create the default output directories for the CubesWriters in play
        for writer in self.writers:
            this_out_path: Path = writer.get_out_path()
            assert isinstance(this_out_path, Path), f'Writer {writer.__name__} is not returning an output path.'
            this_out_path.mkdir(exist_ok=True, parents=True)

        self.base_uri = base_uri
        self.cubes = []
        self.has_ran = False
        self.formatters = formatters
        self._known_formatters = STANDARD_FORMATTERS
        
        if job_name is not None:
            # Another depreciation warning, 5/5/2010. This has been up a while already so aim to remove from roughly 1/7/2021
            logging.warning("The passing of job_name= has been depreciated and no longer does anything, please"
                            "remove this keyword argument")

    # TODO... eventully. <metadata_thing> not <scraper>. An output driver deserves a paired input driver.
    # note - whenw e do have the outputdriver type check the inputdriver for compatibiity, voila, we is decoupled.
    def add_cube(self, scraper, dataframe, title, graph=None, info_json_dict=None, override_containing_graph=None,
            writer_override = None, formatters=None):
        """
        Add a single datacube to the cubes class.
        """

        # If there are no Cube() level formatters fall back on any declared at the Cubes() level
        # If we've got both, use both.
        if not formatters:
            formatters = self.formatters
        elif formatters and self.formatters:
            # TODO - do we need to handle clashes here?
            formatters = {**formatters, **self.formatters}

        self.cubes.append(Cube(self.base_uri, scraper, dataframe, title, graph, info_json_dict,
                               override_containing_graph, writer_override, formatters, self._known_formatters))

    def register_formatters(self, name, writer_class):
        """
        Allow the user to register formatters for CubeWriter classes beyond
        those currently defined in gssutils
        """
        # TODO - think, duplicates, good or bad?
        # do we _want_ to let people override a global applied writer per cube?
        self._known_formatters[name] = writer_class


    def output_all(self, raise_writer_exceptions: bool = True):
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

        # NOTE - the following bit of pre-output logic is very coupled to pmd and graphs, ideally we want to get rid
        # note to self: args, kwargs = <writer>._outer_scope_args() ..possibly, pull it apart.

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
                cube.output(is_multi_cube, is_many_to_one, self.info,
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
                 override_containing_graph_uri: Optional[str], writer_override, formatters, known_formatters):

        self.scraper = copy.deepcopy(scraper)  # note - the metadata of a scrape, not the actual data source
        self.dataframe = dataframe
        self.title = title
        self.scraper.set_base_uri(base_uri)
        self.graph = graph
        self.info_json_dict = copy.deepcopy(info_json_dict)  # don't copy a pointer, snapshot a thing
        self.override_containing_graph_uri = override_containing_graph_uri
        self.formatters = formatters
        self._known_formatters = known_formatters

        # I'm not 100% but it's conceivable that we'll want to output subset of the
        # defined cubes to different places, so we're including a per-cube writer override
        # as a precaution against that eventuality.
        self.writer_override = writer_override


    def output(self, is_multi_cube, is_many_to_one, info_json, writers, raise_writer_exceptions):
        """
        Outputs the required per-platform inputs for a single 'Cube' held in the 'Cubes' object
        """

        # DE knows best
        if self.writer_override:
            writers = self.writer_override

        for writer in writers:
            logging.warning(f'Columns at start of loop {self.dataframe.columns.values}')

            # We're going to catch an error here as one writer output failing shouldn't stop us trying the next
            # note - flagged off while testing, see "raise_writer_exceptions" coming from Cubes.output_all()
            try:
                this_writer = writer(is_multi_cube, is_many_to_one, info_json, cube=self)
                # If we've regstered any formatter fuctions at Cubes() or Cube() level that match
                # the specified writer, attach them here.
                for formatter_name, format_funcs in self.formatters.items():
                    if self._known_formatters[formatter_name] == writer:
                        # Formatters can be either a singleton or a list, force list
                        format_funcs = [format_funcs] if not isinstance(format_funcs, list) else format_funcs
                        for format_func in format_funcs:
                            this_writer.formatters.append(format_func)

                for operation in this_writer.operational_sequence:
                    operation()
            
            except Exception as err:
                logging.error(f'Output failed for writer {writer} with exception:\n {err}') 
                if raise_writer_exceptions:
                    raise err

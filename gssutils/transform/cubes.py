import json
import logging
import os

from pathlib import Path
from urllib.parse import urljoin
import pandas as pd

from gssutils.csvw.mapping import CSVWMapping
from gssutils.csvw.namespaces import URI
from gssutils.csvw.table import Table, ForeignKey, ColumnReference
from gssutils.transform.codelists import generate_codelist_schema
from gssutils.utils import pathify


class IndistinctReferenceError(Exception):
    """ Raised when we're provided more than one definition of the same thing
    """

    def __init__(self, message):
        self.message = message


class Cubes:
    """
    A class representing multiple datacubes
    """

    def __init__(self, info_json="info.json", destination_path="out", codelist_path="codelists",
                 base_url="http://gss-data.org.uk", generate_codelists=False):

        # NOTE - I'm flagging generate_codelists to false (above) for now as it's functionality
        # we don't need/havn't quite bottomed out yet. We should be able to switch the
        # flag back when we get to that task.

        with open(info_json, "r") as info_file:
            self.info = json.load(info_file)

        # Where we don't have a mapping field, add one to avoid iteration errors later
        if "columns" not in self.info["transform"].keys():
            self.info["transform"]["columns"] = []

        self.destination_folder = Path(destination_path)
        self.destination_folder.mkdir(exist_ok=True, parents=True)
        self.codelist_path = codelist_path
        self.base_url = base_url
        self.cubes = []
        self.has_ran = False
        self.generate_codelists = generate_codelists

    def add_cube(self, scraper, dataframe, title, not_a_codelist=["Value"]):
        """
        Add a single datacube to the cubes class. The handling is slightly different
        for every cube after the first, hence the is_multi_cube check.
        """
        is_multi_cube = len(self.cubes) >= 2
        self.cubes.append(Cube(self.base_url, scraper, dataframe, title, is_multi_cube,
                               self.codelist_path, not_a_codelist))

    def output_all(self):
        """
        Output every cube object we've added to the cubes() class.
        """

        if len(self.cubes) == 0:
            raise Exception("Please add at least one datacube with '.add_cube' before "
                            "calling output_all().")

        if self.has_ran:
            raise Exception("Calling 'output_all' on the Cubes class is a destructive process and "
                            "has already run. You need to add all your datacubes before doing so.")

        is_multi_cube = len(self.cubes) >= 2
        for cube in self.cubes:
            try:
                cube.output(self.destination_folder, is_multi_cube, self.info,
                        self.generate_codelists)
            except Exception as err:
                raise Exception("Exception encountered while processing datacube '{}'." \
                                .format(cube.title)) from err
        self.has_ran = True


class Cube:
    """
    A class to encapsulate the dataframe and associated metadata that constitutes a datacube
    """

    def __init__(self, base_url, scraper, dataframe, title, is_multi_cube,
                codelist_path, not_a_codelist):
        self.scraper = scraper
        self.dataframe = dataframe
        self.title = title
        self.codelist_path = codelist_path
        self.codelists = {}
        self.not_a_codelist = not_a_codelist
        self.base_url = base_url
        self.scraper.set_base_uri(self.base_url)

        #---- Trig files ----
        # At some point we'll be moving to just putting all the metadata in the csvw schema file
        # rather than in a seperate trig file.
        #
        # Until we get to the above, we need to generate the trig now in case the selected,
        # distribution changes, but we don't know yet if it's a single datacube or a part of a
        # list of datacubes so for the very first one we'll generate a singleton trig as well.
        if not is_multi_cube:
            # The trig should this cubes class end up generating only a single output
            self.singleton_trig = scraper.generate_trig()

        # Set title and dataset_id, need to do this before generating the multicube variant trig
        # file as these are values that change depending on single vs multiple cube outputs.
        self.scraper.dataset.title = title

        dataset_path = pathify(os.environ.get('JOB_NAME',
            f'gss_data/{self.scraper.dataset.family}/' + Path(os.getcwd()).name)).lower()
        self.scraper.set_dataset_id(dataset_path)

        # The trig for this cube if it's one cube of many
        self.multi_trig = scraper.generate_trig()

    def _get_prefabricated_codelists(self):
        """
        Read in any codelists.csvs already present in the chosen codelists directory.
        """

        # if the chosen codelists directory doesnt exists, create it and be loud about it
        if not os.path.isdir(self.codelist_path):
            logging.warning('You have the codelist directory set to "{}" but '
                            'that directory does not exist'.format(self.codelist_path))

            logging.warning('Creating "{}" directory'.format(self.codelist_path))
            Path(self.codelist_path).mkdir(exist_ok=True, parents=True)
            return

        # get all the codelists into our self.codelists {name:dataframe} dictionary
        codelist_files = [f for f in os.listdir(self.codelist_path) if
                          os.path.isfile(Path(self.codelist_path, f)) and
                          f.endswith(".csv")]

        # blow up for multiple definitions of the same thing
        if len(codelist_files) != len(set(codelist_files)):
            raise IndistinctReferenceError("A codelist can only be defined once. Have '{}'."
                                           .format(",".join(codelist_files)))

        for codelist_file in codelist_files:
            read_from = os.path.join(self.codelist_path, codelist_file)
            self.codelists[codelist_file[:-4]] = pd.read_csv(read_from)

    def _instantiate_map(self, destination_folder, pathified_title, info_json):
        """
        Create a basic CSVWMapping object for this cube
        """
        map_obj = CSVWMapping()
        map_obj.set_mapping(info_json)
        map_obj.set_csv(destination_folder / f'{pathified_title}.csv')
        map_obj.set_dataset_uri(urljoin(self.scraper._base_uri, f'data/{self.scraper._dataset_id}'))

        return map_obj

    def _write_default_codelist(self, unique_values, column_label):
        """
        Given a list of values (a column of a csv) build a default codelist
        as a dataframe then write it.
        """
        dataframe = self._build_default_codelist(unique_values)
        write_to = os.path.join(self.codelist_path, column_label)
        dataframe.to_csv("{}.csv".format(write_to), index=False)
        return dataframe

    def _build_default_codelist(self, unique_values):
        """
        Given a list of values (a column of a csv) build a default codelist
        as a dataframe.
        """

        unique_values = list(set(unique_values))

        codelist = {
            "Label": unique_values,
            "Notation": [pathify(x) for x in unique_values],
        }
        dataframe = pd.DataFrame().from_dict(codelist)
        dataframe["Parent Notation"] = ""
        dataframe["Sort Priority"] = ""
        dataframe["Description"] = ""

        return dataframe

    def _generate_codelist_and_schema(self, column_label, destination_folder, dataframe=None):
        """
        Output a given codelists, using the user provided one by preference, but fall
        through to a default one where its not.
        """
        if dataframe is None:
            dataframe = self._write_default_codelist(self.dataframe[column_label], column_label)

        # output codelist csv
        dataframe.to_csv(destination_folder / "codelist-{}.csv".format(pathify(column_label)), 
                index=False)

        # output codelist schema
        generate_codelist_schema(column_label, destination_folder, self.base_url, self.title)

        # return tableschema
        return Table(
            url=URI("codelist-{}.csv".format(pathify(column_label))),
            tableSchema="codelist-{}.csv-schema-json".format(pathify(column_label))
        )

    def _get_trig(self, is_multi_cube):
        """
        Get the trig being used, this can vary depending on whether this is a single or
        multiple datacube output
        """
        if not is_multi_cube:
            return self.singleton_trig
        return self.multi_trig

    def _populate_csvw_mapping(self, destination_folder, pathified_title,
                        info_json, generate_codelists):
        """
        Use the provided details object to generate then fully populate the mapping class
        """

        # The base CSVWmapping class
        map_obj = self._instantiate_map(destination_folder, pathified_title, info_json)

        # Add all the additional details around codelist and foreign keys
        # ...if... generate_codelists is flagged True
        if generate_codelists:

            self._get_prefabricated_codelists()

            additional_tables = []
            foreign_keys = []
            for column_label in [x for x in self.dataframe.columns.values if x not in self.not_a_codelist]:
                codelist_df = self.codelists.get(column_label, None)
                additional_tables.append(
                    self._generate_codelist_and_schema(column_label, destination_folder,
                            dataframe=codelist_df))
                foreign_keys.append(
                    ForeignKey(
                        columnReference=pathify(column_label),
                        reference=ColumnReference(
                            resource=URI("codelist-{}.csv".format(pathify(column_label))),
                            columnReference="notation"
                        )
                    )
                )

            for additional_table in additional_tables:
                map_obj._external_tables.append(additional_table)
            for foreign_key in foreign_keys:
                map_obj.set_additional_foreign_key(foreign_key)

        return map_obj

    def output(self, destination_folder, is_multi_cube, info_json, generate_codelists):
        """
        Outputs the csv and csv-w schema for a single 'Cube' held in the 'Cubes' object
        """
        pathified_title = pathify(self.title)

        # output the tidy data
        self.dataframe.to_csv(destination_folder / f'{pathified_title}.csv', index=False)

        # Output the trig
        trig_to_use = self._get_trig(is_multi_cube)
        with open(destination_folder / f'{pathified_title}.csv-metadata.trig', 'wb') as metadata:
            metadata.write(trig_to_use)

        # Output csv and csvw
        populated_map_obj = self._populate_csvw_mapping(destination_folder, pathified_title, 
                                info_json, generate_codelists)
        populated_map_obj.write(destination_folder / f'{pathified_title}.csv-metadata.json')


import json

from pathlib import Path
import logging
from os import environ
import pandas as pd

from gssutils.scrape import MetadataError
from gssutils.utils import pathify
from gssutils.csvw.t2q import CSVWMetadata

from gssutils.csvw.mapping import CSVWMapping


class Cubes(object):
    """
    A class representating multiple datacubes
    """
    def __init__(self, info_json, ref_path=None, out_path="out", not_a_codelist=[]):
    
        with open(info_json, "r") as f:
            self.info = json.load(f)

        # vaidate all the things

        # TODO - add a blank columns to airtable sync
        # for now, add it where missing
        if "columns" not in self.info["transform"].keys():
            self.info["transform"]["columns"] = []

        self.ref_path = ref_path
        self.destination_folder = Path(out_path)
        self.destination_folder.mkdir(exist_ok=True, parents=True)
        self.not_a_codelist = not_a_codelist
        
        self.cubes = []
        self.has_ran = False
    
    def add_cube(self, distribution, dataframe, title, ignore_codelists=["Value"]):
        is_multiCube = False if len(self.cubes) < 2 else True
        self.cubes.append(Cube(distribution, dataframe, title, is_multiCube,
                            ignore_codelists))
            
    def output_all(self, with_transform=False, mapping=None, base_url="http://gss-data.org.uk", 
                    base_path=None, dataset_metadata=None, with_external=None):
        
        if len(self.cubes) == 0:
            raise Exception("Please add at least one datacube with '.add_cube' before "
                           "calling output_all().")
    
        if self.has_ran:
            raise Exception("Calling 'output_all' on the Cubes class is a destructive process and "
                            "has already run. You need to add all your datacubes before doing so.")
                
        is_multiCube = False if len(self.cubes) < 2 else True
        for process_order, cube in enumerate(self.cubes):
            try:
                cube._output(process_order, self.ref_path, self.destination_folder, is_multiCube, 
                            with_transform, mapping, base_url, base_path, dataset_metadata, with_external,
                            self.info)
            except Exception as e:
                raise Exception("Exception encountered while processing datacube '{}'." \
                               .format(cube.title)) from e
        self.has_ran = True
                          

class Cube(object):
    """
    A class to encapsulate the dataframe and associated metadata that constitutes a datacube
    """
    def __init__(self, scraper, dataframe, title, is_multiCube, ignore_codelists, codelists={}):
        self.scraper = scraper
        self.df = dataframe
        self.title = title
        self.codelists = codelists
        self.ignore_codelists = ignore_codelists

        # We need to track the sequence the cubes are processsed in, this allows 
        # us to confirm correct namespacing
        self.process_order = None
            
        # ---- Trig files ----:
        # We need to generate the trig now in case the selected distribution changes,
        # but we don't know yet if it's a single datacube or a part of a list of datacubes
        # so for the very first one we'll generate a singleton trig as well.
        if not is_multiCube:
            # The trig should this script generate a single output
            self.singleton_trig = scraper.generate_trig()
        
        # The trig for this cube in a multicube:
        self.scraper.dataset.title = title
        self.scraper.set_dataset_id(f'{pathify(environ.get("JOB_NAME", ""))}/{pathify(title)}')
        self.multi_trig = scraper.generate_trig()
           
    def instantiate_map(self, destination_folder, pathified_title, info_json):
        """
        Create a CSVWMapping object for this cube from the info.json provided
        """
        mapObj = CSVWMapping()
        mapObj.set_mapping(info_json)
        mapObj.set_csv(destination_folder / f'{pathified_title}.csv')
        mapObj.set_dataset_uri(pathified_title)

        return mapObj

    def _build_default_codelist(self, unique_values):
        """
        Given a list of values (a column of a csv) build a default codelist
        """
        
        # just in case
        if len(set(unique_values)) != len(unique_values):
            unique_values = set(unique_values)

        cl = {
            "Label": [x for x in unique_values],
            "Notation": [pathify(x) for x in unique_values],
        }
        df = pd.DataFrame().from_dict(cl)
        df["Parent Notation"] = ""
        df["Sort Priority"] = ""
        df["Description"] = ""

        return df

    def _output_codelist(self, column_label, destination, df=None):
        """
        Output a given codelists, using the user provided one by preference, but fall
        through to a default one where its not.
        """
        if df is None:
            df = self._build_default_codelist(self.df[column_label])
        df.to_csv(destination / "codelist-{}.csv".format(pathify(column_label)), index=False)
        self._generate_codelist_schema(destination, column_label, df)


    def _generate_codelist_schema(self, destination, column_label, df):
        """
        Given a codelist in the form of a dataframe, generate a codelist schema
        """
        columns = []
        for column in df.columns.values:
            pass

        # TODO - fugly
        table_schema = {
            "url": "codelist-{}-schema.json".format(pathify(column)),
            "columns": columns,
            "rdfs:label": "Code list for {} codelist scheme".format(column),
            "rdf:type": "skos:ConceptScheme",
            "skos:prefLabel": "Code list for {} codelist scheme".format(column),
            "qb:codelist": "http://gss-data.org.uk/def/concept-scheme/{}/{}" \
                            .format(pathify(self.title), pathify(column))
        }

        schema_path = Path(destination / "codelist-{}.schema-json".format(pathify(column_label)))
        with open(schema_path, "w") as f:
            f.write(json.dumps(table_schema))


    def _output(self, process_order, ref_path, destination_folder, is_multiCube, with_transform,
                                mapping, base_url, base_path, dataset_metadata, with_external, info_json):
        """
        Generates the output for a single 'Cube' held in the 'Cubes' object
        """
        base_path = pathify(self.title)
        
        self.process_order = process_order
        
        # sort out which trig snapshot to use
        pathified_title = None
        trig_to_use = None 
        if not is_multiCube:
            pathified_title = "observations"
            trig_to_use = self.singleton_trig
        else:
            pathified_title = pathify(self.scraper.dataset.title)
            trig_to_use = self.multi_trig
        
        # output the tidy data
        self.df.to_csv(destination_folder / f'{pathified_title}.csv', index = False)

        # generate codelist csvs and schemas
        for col in [x for x in self.df.columns.values if x not in self.ignore_codelists]:
            codelist_df = self.codelists.get(col, None)
            self._output_codelist(col, destination_folder, df=codelist_df)

        with open(destination_folder / f'{pathified_title}.csv-metadata.trig', 'wb') as metadata:
            metadata.write(trig_to_use)

        mapObj = self.instantiate_map(destination_folder, pathified_title, info_json)
        mapObj.write(destination_folder / f'{pathified_title}.csv-schema.json')


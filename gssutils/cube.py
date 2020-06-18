
from pathlib import Path
import logging
from os import environ

from gssutils.scrape import MetadataError
from gssutils.utils import pathify
from gssutils.csvw.t2q import CSVWMetadata


class Cubes(object):
    """
    A class representating multiple datacubes
    """
    def __init__(self, ref_path, out_path="out", meta_dict={}):
    
        self.ref_path = ref_path
        self.destination_folder = Path(out_path)
        self.destination_folder.mkdir(exist_ok=True, parents=True)
        
        self.cubes = []
        self.has_ran = False
    
        # allow direct passing of metadata (in case of old url-only pipelines) but
        # moan about it (we should really be using info.json)
        self.meta_dict = meta_dict
        if len(self.meta_dict) != 0:
               logging.warning("Metadata being passed to 'Cubes' via a dictionary - you should "
                               "be using the seed for this via info.json.")
    
    def add_cube(self, distribution, dataframe, title):
        is_multiCube = False if len(self.cubes) < 2 else True
        self.cubes.append(Cube(distribution, dataframe, title, self.meta_dict, is_multiCube))
            
    def output_all(self, with_transform=True):
        
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
                            with_transform)
            except Exception as e:
                raise Exception("Exception encountered while processing datacube {}" \
                               .format(cube.title)) from e
        self.has_ran = True
                          
                          
class Cube(object):
    """
    A class to encapsulate the dataframe and associated metadata that constitutes a datacube
    """
    def __init__(self, scraper, dataframe, title, meta_dict, is_multiCube):
        self.scraper = scraper
        self.df = dataframe
        self.title = title

        # We need to track the sequence the cubes are processsed in, this allows 
        # us to confirm correct namespacing
        self.process_order = None
        
        # Make sure we have the required metadata, fill in where missing
        for attr_name in ["family", "theme"]:
            self._check_add_attribute(attr_name, meta_dict)
            
        # ---- Trig files ----:
        # We need to generate the trig now in case the selected distribution changes,
        # but we don't know yet if it's a single datacube or a part of a list of datacubes
        # so for the very first run we'll generate a singleton trig as well.
        
        # TODO - when mapping comes in we'll be storing the data that -would- populate a
        # trig (for padding the csvw) rather than generating a .trig() directly.
        
        if not is_multiCube:
            # The trig should this script generate a single output
            self.singleton_trig = scraper.generate_trig()
        
        # The trig for this cube in a multicube:
        self.scraper.dataset.title = title
        self.scraper.set_dataset_id(f'{pathify(environ.get("JOB_NAME", ""))}/{pathify(title)}')
        self.multi_trig = scraper.generate_trig()
        
            
    def _check_add_attribute(self, attr_name, meta_dict):
        if not hasattr(self.scraper.dataset, attr_name):
            
            try_dict = True
            if self.scraper.seed is not None:
                if attr_name in self.scraper.seed.keys():
                    self.scraper.dataset.__setattr__(attr_name, self.scraper.seed[attr_name])
                    try_dict = False
                    
            if try_dict and attr_name in meta_dict.keys():
                self.scraper.dataset.__setattr__(attr_name, meta_dict[attr_name])
            else:
                raise MetadataError(f"A '{attr_name}' attribute is required and is not present " 
                                "in the seed and has not been passed in at run time")
        

    def _output(self, process_order, ref_path, destination_folder, is_multiCube, with_transform):
        
        self.process_order = process_order
        
        pathified_title = None
        trig_to_use = None 
        if not is_multiCube:
            pathified_title = "observations"
            trig_to_use = self.singleton_trig
        else:
            pathified_title = pathify(self.scraper.dataset.title)
            trig_to_use = self.multi_trig
        
        self.df.to_csv(destination_folder / f'{pathified_title}.csv', index = False)

        with open(destination_folder / f'{pathified_title}.csv-metadata.trig', 'wb') as metadata:
            metadata.write(trig_to_use)

        # Using table2cube
        if not with_transform:
            schema = CSVWMetadata(ref_path)
            schema.create(destination_folder / f'{pathified_title}.csv', destination_folder / \
                          f'{pathified_title}.csv-schema.json')
        
        # Using csv2rdf
        else:
            raise NotImplementedError("Awaiting pending change of of approach RE mapping files for RDF.")
            
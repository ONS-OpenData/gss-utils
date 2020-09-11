
import os
import uuid
import json
import shutil
import logging

from jinja2 import Template, TemplateError
from datetime import datetime
from pathlib import Path
from databaker.framework import savepreviewhtml
import pandas as pd
import requests

from gssutils.utils import pathify

PREVIEW_NOTE = " -- Preview created -- "


def excelRange(bag):
    """Get the furthermost tope-left and bottom-right cells of a given selection"""
    min_x = min([cell.x for cell in bag])
    max_x = max([cell.x for cell in bag])
    min_y = min([cell.y for cell in bag])
    max_y = max([cell.y for cell in bag])
    top_left_cell = xypath.contrib.excel.excel_location(bag.filter(lambda x: x.x == min_x and x.y == min_y))
    bottom_right_cell = xypath.contrib.excel.excel_location(bag.filter(lambda x: x.x == max_x and x.y == max_y))
    return f"{top_left_cell}:{bottom_right_cell}"

class CubeSegment(object):
    """
    An object representing the actions taken upon a single conversion segment
    or dataframe.
    """
    def __init__(self, cube_name, tab, source):
        self.cube_name = cube_name
        self.tab = tab
        self.source = source
        self.columns = {}
        self.preview = None
        self.obs = None

    def add_column(self, column):
        
        alias = None
        if isinstance(column, dict):
            column, alias = next(iter(column.items()))
            
        if alias is None:
            alias = column.replace("-", "_").replace(" ", "_")
            
        self.columns[alias] = Column(column)
        setattr(TransformTrace, alias, self.columns[alias])


class Column(object):
    """
    An object representing the documentation of changes made to a column (or pre-column)
    of data within a dataset
    """

    def __init__(self, column):
        
        self.label = column
        self.comments = []
        self.var = None

    def __call__(self, comment, var=None, excelRange=None):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        if var is not None and excelRange is not None:
            raise Exception("Aborting. 'excelRange' is a means of populating the 'var keyword argument."
                            "Therefore you cannot pass both 'excelRange' and 'var' in the same constructor")
        
        elif var is not None:
            self.var = var
            comment = comment.format(self.var)
        elif excelRange is not None:
            self.var = excelRange(excelRange)
            comment = comment.format(self.var)

        self.comments.append({now: comment})


class TransformTrace(object):
    """
    An object representing documentation of changes made to a dataset
    """

    def __init__(self):
        self.cubes = {}
        self.composite_key = None
        self.df_store = {}
        self.all_composite_keys = []
        
        # Track warnings - we don't want to trigger them over
        # and over when we loop tabs etc
        self.warned = []

        # Remove any lingering documentation from the last run
        if os.path.exists("documentation"):
            shutil.rmtree("documentation")

    def _set_composite_key(self, cube_name, tab_name, source):
        if isinstance(source, list):
            source = "".join(source)

        self.composite_key = cube_name+"||"+tab_name+"||"+source
        self.all_composite_keys.append(self.composite_key)

    def start(self, cube_name, tab, columns, source):
        """
        Create and set a cube/conversion segment to the currently tracked object
        """

        # Allow populate tab_name as explicit string (for combined cubes)
        self.tab_name = tab if isinstance(tab, str) else tab.name

        # Unset the old column attributes before we change the active cube
        if self.composite_key is not None:
            for column in self.cubes[self.composite_key].columns.keys():
                delattr(TransformTrace, column)

        self._set_composite_key(cube_name, self.tab_name, source)
        self.cubes[self.composite_key] = CubeSegment(cube_name, self.tab_name, source)
        for column in columns:
            self.add_column(column)

    # Depreciating - should never have used caps
    def OBS(self, comment):
        if "OBS" not in self.warned:
            logging.warning('We\'re depreciating the ".OBS" command, please use the standards-compliant ".obs" instead.')
            self.warned.append("OBS")
        self.cubes[self.composite_key].obs = comment
        
    def obs(self, comment):
        self.cubes[self.composite_key].obs = comment

    def add_column(self, column):
        self.cubes[self.composite_key].add_column(column)

    def multi(self, columns, comment):
        """
        An action that applies to each column listed in columns
        """
        for column in columns:
            self.cubes[self.composite_key].columns[column](comment)

    # Depreciating - should never have used caps
    def ALL(self, comment):
        """
        An action that applies to all columns
        """
        if "ALL" not in self.warned:
            logging.warning('We\'re depreciating the ".OBS" command, please use the standards-compliant ".obs" instead.')
            self.warned.append("ALL")
            self.ALL(comment)

    def all(self, comment):
        for columnObj in self.cubes[self.composite_key].columns.values():
            columnObj('ALL: '+comment)

    def store(self, identifier, df):
        if identifier not in self.df_store.keys():
            self.df_store.update({identifier: []})
        self.ALL("Stored under the identifier '{}'".format(identifier))

        tab  = self.cubes[self.composite_key].tab

        # Listify multiple sources with the tab name
        source = self.cubes[self.composite_key].source
        if isinstance(source, list):
            source = [x+" : "+tab for x in source]

        self.df_store[identifier].append({
                    "composite_key": self.composite_key,
                    "tab": self.cubes[self.composite_key].tab,
                    "source": source,
                    "df": df})

    def combine_and_trace(self, cube_name, identifier):
        if identifier not in self.df_store.keys():
            raise Exception("{} does not identify a list of dataframes.".format(identifier))

        if cube_name in self.cubes.keys():
            raise Exception("Each datacube must have a unique identifier, you have already "
                           "used the identifier '{}'.".format(cube_name))

        # Add an action against all columns of all cubes that are being joined
        composite_keys = []
        dfs = []
        source = []
        for stored_item in self.df_store[identifier]:
                composite_keys.append(stored_item["composite_key"])
                dfs.append(stored_item["df"])
                source.append(stored_item["source"] + " : " + stored_item["tab"])

        columns = []
        for composite_key in composite_keys:
            for columnObj in self.cubes[composite_key].columns.values():
                if columnObj.label not in columns:
                    columns.append(columnObj.label)
                columnObj("Added to dataframe '{}'".format(identifier))
                
        self.start(cube_name, identifier, columns, source)

        return pd.concat(dfs, sort=False)

    def with_preview(self, cs):
        path_to_preview = 'documentation/previews'
        destinationFolder = Path(path_to_preview)
        destinationFolder.mkdir(exist_ok=True, parents=True)

        path_to_preview_file = "{}/{}.html".format(path_to_preview, str(uuid.uuid4()))
        savepreviewhtml(cs, fname=path_to_preview_file)
        self.cubes[self.composite_key].preview = path_to_preview_file

        self.ALL(PREVIEW_NOTE)

    def _create_output_dict(self):
        outputs = {}

        # Group by unique cube names
        cube_names = list(set([x.cube_name for x in self.cubes.values()]))
        for cube_name in cube_names:
            output = {}
            for composite_key, cubeObj in {k: v for k,v in self.cubes.items() if v.cube_name == cube_name}.items():
                columns_info = []
                for column_id, columnObj in cubeObj.columns.items():
                    column_info = {
                        "column_id": column_id,
                        "column_label": columnObj.label,
                        "actions": []
                    }
                    for comment_dict in columnObj.comments:
                        column_info["actions"].append(comment_dict)
                    columns_info.append(column_info)

                sid = cubeObj.tab if isinstance(cubeObj.source, list) else \
                            "{} : {}".format(cubeObj.source, cubeObj.tab)

                output = {
                    "composite_key": composite_key,
                    "sourced_from": cubeObj.source,
                    "id": sid,
                    "tab": cubeObj.tab,
                    "column_actions": columns_info
                }
                if cubeObj.preview is not None:
                    output.update({"preview": cubeObj.preview})
                if cubeObj.obs is not None:
                    output.update({"observations": cubeObj.obs})

                if cube_name not in outputs.keys():
                    outputs.update({cube_name: []})
                outputs[cube_name].append(output)
        return {cube_name: outputs}

    # DEVNOTE: I've switched this off, the raw traced output_dict is accessible via
    # the renderer so no particular reason we need a hard copy.
    def _write_output_dict(self, output_dict):
        destinationFolder = Path('documentation')
        destinationFolder.mkdir(exist_ok=True, parents=True)

        for dataset_details in output_dict.values():
            for cube_name, details in dataset_details.items():
                output = {cube_name: details}
                with open("documentation/{}.json".format(pathify(cube_name)), "w") as f:
                    json.dump(output, f, indent=4)

    def _update_transform_stage(self, output_dict):
        
        with open("info.json", "r") as f:
            data = json.load(f)
            data["transform"]["transformStage"] = []

            # Get the identifier for each cube segment being traced (i.e each tab or combined tab)
            for trace_key in self.all_composite_keys:

                # get the 'CubeSegment' class for it: ... scroll up for class definition
                cube_segment = self.cubes[trace_key]

                columns = []
                extraction_note = []
                for column_name, columnObj in cube_segment.columns.items():
                    columns.append({
                        # take the comments, but without the time stamp
                        column_name: [next( v for k,v in x.items()) for x in columnObj.comments]
                    })
                    if columnObj.var is not None:
                        extraction_note.append({columnObj.label: columnObj.var})

                source = cube_segment.source
                if not isinstance(source, list):
                    source = [source]
                split_source = []
                for s in source:
                    s_href = s.split(" : ")[0]
                    # Not all sources have comments, account for it
                    try:
                        s_text = s.split(" : ")[1]
                    except IndexError:
                        s_text = ""
                    split_source.append({s_href: s_text})

                # TODO - column name isn't necessarily unique
                update = {
                    "source_name": cube_segment.cube_name,
                    "identifier": trace_key,
                    "source": split_source,
                    "title": cube_segment.tab,
                    "preview": cube_segment.preview,
                    "observation_selection": cube_segment.obs,
                    "columns": extraction_note,
                    "postTransformNotes": columns
                    }

                data["transform"]["transformStage"].append(update)

        with open("info.json", "w") as f:
            json.dump(data, f, indent=4)

        return data

    def output(self):
        logging.warning("We're depreciated .output() can you use .render() instead please, " \
                        "if you use if with no arguments it'll get you to the same place.")
        self.render()

    def render(self, template=None, output="./out/spec.html", foreign_sources={}, local=None, local_sources=None):
        """
        With no parameters render will update the info.json with the transformation information
        with params we'll render a html inline.
        """
        
        # base data sources
        raw_data = self._create_output_dict()
        info_json = self._update_transform_stage(raw_data) 

        # we also need some basic jenkins details
        # Jenkins is case sensitive, and the pattern si different for covid
        family = info_json["families"][0].lower()
        if "COVID" in family.upper():
            family = family.upper()
        else:
            family = "-".join([x.capitalize() for x in family.split("-")])

        # Jenkins Job ---------
        # TODO - this bits very unlikely to be robust, but only matters for running
        # locaally.... sometimes is better than never
        jenkins_title = info_json["title"].replace(",", "").replace(" ", "-")
        pub_name = info_json["publisher"].split(" ")
        try:
            jenkins_title = pub_name[0] + "-" + pub_name[1][:1] + "-" + jenkins_title
        except IndexError:
            jenkins_title = pub_name[0] + jenkins_title

        jenkins_job = pathify(os.environ.get('JOB_NAME', f'replace-with-family-name/job/')) + jenkins_title
        jenkins_job = jenkins_job.replace("replace-with-family-name", family)
        jenkins = {
            "job": jenkins_job,
            "family": family
        }

        # Jenkins Build Status ---------
        jenkins_build = f"https://ci.floop.org.uk/buildStatus/icon?job=GSS_data%2F{family}%2F{jenkins_title}/"
        jenkins["build"] = jenkins_build

        if local is not None and template is not None:
            raise Exception("You can only pass EITHER local= or a remote template url/name, not both")

        # Templating, going to wrap this in case something goes bang
        try:

            if local is not None:
                try:
                    with open(local, "r") as f:
                        localTemplate = f.read()
                except Exception as e:
                    raise Exception("Unable to open template from location {}.".format(local)) from e
            elif template is None:
                # Exit immediately if no local template and we don't want to render
                return
            elif "/" not in template:
                # If it's just a file name so it's a template from the standard library
                template = "https://raw.githubusercontent.com/GSS-Cogs/frontend-template-resources/master/templates/jinja2/"+template
            else:
                pass

            """
            A foreign source is where we want to call in a little more data for the renderer,
            We'll add them to the two existing data sources we always make availible, which are:

            info_json: the info.json
            raw_data: the dictionary that is the tracer store (similar but with a little extra info)
            """
            kwargs = {
                "info_json": info_json,
                "raw_data": raw_data,
                "jenkins": jenkins
            }
            for template_referal, url in foreign_sources.items():
                
                # template_referal is how we want to refer to this exta data
                # in the template. Make sure it's not overwriting a standard data key
                if template_referal in ["info_json", "raw_data"]:
                    raise Exception("Aborting, you cannot pass a data source with the protected " \
                                    "label of {}.".format(template_referal))

                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception("Unable to additional data from: {}, status code {}".format(url, r.status_code))

                kwargs[template_referal] = r.json()

            # the user might also pass in some additional dictionaries
            if local_sources is not None:
                for template_referal, extra_dict in local_sources.items():
                
                    # template_referal is how we want to refer to this exta data
                    # in the template. Make sure it's not overwriting a standard data key
                    if template_referal in ["info_json", "raw_data"]:
                        raise Exception("Aborting, you cannot pass a data source with the protected " \
                                        "label of {}.".format(template_referal))

                    kwargs[template_referal] = extra_dict
           
            if local is None:
                r = requests.get(template)
                if r.status_code != 200:
                    raise Exception("Unable to http get template from: {}, status code {}".format(template, r.status_code))
                templateRenderer = Template(r.text)
            else:
                templateRenderer = Template(localTemplate)
            outputText = templateRenderer.render(**kwargs)
            
            with open(output, "w") as f:
                f.write(outputText)

            print("Template {} rendered as {}".format(template, output))

        except Exception as e:
            raise TemplateError("Problem encountered attmepting to render template") from e


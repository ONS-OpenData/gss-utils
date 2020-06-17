
import os
import uuid
import json
import shutil

from datetime import datetime
from pathlib import Path
from databaker.framework import savepreviewhtml
import pandas as pd

from gssutils.utils import pathify

PREVIEW_NOTE = " -- Preview created -- "


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

    def __call__(self, comment, var=None):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        if var is not None:
            self.var = var
            comment = comment.format(var)
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

    def OBS(self, comment):
        self.cubes[self.composite_key].obs = comment

    def add_column(self, column):
        self.cubes[self.composite_key].add_column(column)

    def multi(self, columns, comment):
        """
        An action that applies to ach column listed in columns
        """
        for column in columns:
            self.cubes[self.composite_key].columns[column](comment)

    def ALL(self, comment):
        """
        An action that applies to all columns
        """
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

    def _write_output_dict(self, output_dict):
        destinationFolder = Path('documentation')
        destinationFolder.mkdir(exist_ok=True, parents=True)

        for dataset, dataset_details in output_dict.items():
            for cube_name, details in dataset_details.items():
                output = {cube_name: details}
                with open("documentation/{}.json".format(pathify(cube_name)), "w") as f:
                    json.dump(output, f)

    def _create_html_output(self, output_dict):

        colour_pick = 0
        def next_colour():
            # Vary table colour for readibility
            pallette = {
                0: "#8cd98c",
                1: "#99b3e6",
                2: "#ffdf80"
            }
            nonlocal colour_pick
            if colour_pick == len(pallette)-1:
                colour_pick = 0
            else:
                colour_pick +=1
            return pallette[colour_pick]

        for dataset, dataset_details in output_dict.items():
            for title, details in dataset_details.items():
                html_lines = []
                html_lines.append("<h3>{}</h3>".format(title))
                for detail in details:
                        html_lines.append("<hr>")
                        html_lines.append("<br>")
                        table_colour = next_colour()
                        html_lines.append("<strong>identifier</strong>    : {}<br>".format(detail["id"]))

                        if "tab" in detail.keys():
                            html_lines.append("<strong>tab</strong>    : {}<br>".format(detail["tab"]))

                        if isinstance(detail["sourced_from"], list):
                            html_lines.append("<strong>sourced from</strong>:<br>")
                            for source in detail["sourced_from"]:
                                html_lines.append(source + "<br>")
                        else:
                            html_lines.append("<strong>sourced_from</strong>   : {}<br>".format(detail["sourced_from"]))

                        if "preview" in detail.keys():
                            html_lines.append("<strong>preview</strong>       : <a href={}>{}</a><br>".format(detail["preview"][14:], detail["preview"][14:]))
                        if "observations" in detail.keys():
                            html_lines.append("<strong>observation selection</strong>   : {}<br>".format(detail["observations"]))

                        html_lines.append("<br>")
                        if "column_actions" in detail.keys():
                            if len(detail["column_actions"]) > 0:
                                for column_data in detail["column_actions"]:
                                    html_lines.append('<table class="fixed">')
                                    html_lines.append("""<col width="200px" /><col width="1000px" />""")
                                    html_lines.append('<th style="background-color:{}" colspan="2">{}</th>'.format(table_colour, column_data["column_label"]))
                                    for action in column_data["actions"]:
                                        for time_stamp, comment in action.items():
                                            html_lines.append("""<tr>
                                                <td>{}</td>
                                                <td>{}</td>
                                                </tr>""".format(time_stamp, comment))
                                    html_lines.append("</table>")
                                    html_lines.append("<br>")
                                html_lines.append("<br>")

                with open(Path('documentation') / "{}.html".format(pathify(title)), "w") as f:
                    f.write("""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                    fixed, th, td {
                        border: 1px solid black;
                    }
                    tr {
                        background-color: white;
                        color: black;
                    }
                    table-layout:fixed
                    </style>
                    </head>
                    <body>""")
                    for line in html_lines:
                        f.write(line + "\n")
                        f.write("""
                                </body>
                                </html>
                                """)

    def output(self, with_html=True):
        output_dict = self._create_output_dict()
        self._write_output_dict(output_dict)
        if with_html:
            self._create_html_output(output_dict)

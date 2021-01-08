"""
A script which aides in the creation and maintainance of `.csv-metadata.json` schema files.

Call with `--help` arg for further instructions.
"""

import json
import glob
from typing import List
import argparse

from .createnew import create_metadata_shell_for_csv
from .applyupdates import refactor_structure_with_updates


def codelist_manager():
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auto", help="Automatically process upgrades without human input.", action='store_true')
    parser.add_argument("-c", "--csv",
                        help="A CSV file. The script will create a corresponding `.csv-metadata.json` file.",
                        type=str, default=None)
    parser.add_argument("-s", "--schema", help="An individual schema file to upgrade.", type=str, default=None)
    parser.add_argument("-u", "--upgrade-all",
                        help="Finds all `.csv-metadata.json` files within the current directory (it recursively "
                             "searches through sub-directories) and applies any upgrades required.",
                        action='store_true')
    args = parser.parse_args()

    metadata_files: List[str]
    if args.schema is not None:
        metadata_files = [args.schema]
    elif args.upgrade_all:
        metadata_files = glob.glob("**/*.csv-metadata.json", recursive=True)
    elif args.csv is not None:
        if args.auto:
            raise Exception("Cannot create a new metadata file from an existing CSV without human input.")
        metadata_files = [create_metadata_shell_for_csv(args.csv)]
    else:
        parser.print_help()
        exit()

    for metadata_file in metadata_files:
        with open(metadata_file, 'r') as file:
            csvw_mapping = json.loads(file.read())

        refactor_structure_with_updates(csvw_mapping, not args.auto)

        config_json = json.dumps(csvw_mapping, indent=4)
        with open(metadata_file, 'w') as file:
            file.write(config_json)


if __name__ == "__main__":
    codelist_manager()

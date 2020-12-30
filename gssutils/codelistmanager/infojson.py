from typing import Optional, Dict
from os import path
import json


def find_maybe_info_json_nearest_file(file_path: str) -> Optional[Dict]:
    if not path.isabs(file_path):
        file_path = path.abspath(file_path)

    [file_directory, _] = path.split(file_path)
    return find_maybe_info_json(file_directory)


def find_maybe_info_json(absolute_directory_path: str) -> Optional[Dict]:
    """
    Recursively search parent folders to find the closest info.json file.
    """

    possible_info_json_path = path.join(absolute_directory_path, "info.json")
    if path.exists(possible_info_json_path):
        with open(possible_info_json_path, 'r') as file:
            return json.loads(file.read())

    path_parts = path.split(absolute_directory_path)
    if len(path_parts) == 1:
        return None

    [parent_dir, _] = path_parts

    return find_maybe_info_json(parent_dir)

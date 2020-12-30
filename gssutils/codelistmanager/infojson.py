from typing import Optional, Dict
from os import path
import json


def find_maybe_info_json_nearest_file(file_path: str) -> Optional[Dict]:
    if not path.isabs(file_path):
        file_path = path.abspath(file_path)

    [file_directory, _] = file_path.split()
    return find_maybe_info_json(file_directory)


def find_maybe_info_json(absolute_directory_path: str) -> Optional[Dict]:
    """
    Recursively search parent folders to find the closest info.json file.
    """
    possible_info_json_path = path.join(absolute_directory_path, "info.json")
    if path.exists(possible_info_json_path):
        return json.load(possible_info_json_path)

    [parent_dir, _] = path.split(absolute_directory_path)
    if len(parent_dir) == 0:
        return None

    return find_maybe_info_json(parent_dir)

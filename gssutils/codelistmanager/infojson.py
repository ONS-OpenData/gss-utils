from typing import Optional, Dict
from pathlib import Path
import json


def find_maybe_info_json_nearest_file(file_path: Path) -> Optional[Dict]:
    if not file_path.is_absolute():
        file_path = file_path.absolute()

    return find_maybe_info_json(file_path.parent)


def find_maybe_info_json(absolute_directory_path: Path) -> Optional[Dict]:
    """
    Recursively search parent folders to find the closest info.json file.
    """

    possible_info_json_path = absolute_directory_path.joinpath("info.json")
    if possible_info_json_path.exists():
        with open(possible_info_json_path, 'r') as file:
            return json.loads(file.read())

    if len(absolute_directory_path.parts) == 1:
        return None

    return find_maybe_info_json(absolute_directory_path.parent)

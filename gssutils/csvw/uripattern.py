from typing import List
from uritemplate import URITemplate


class URIPattern:

    def __init__(self):
        self.regexes = List[str]
        self.templates: List[URITemplate] = []

    def formats(self):
        for t in self.templates:
            t.variables
        return {}
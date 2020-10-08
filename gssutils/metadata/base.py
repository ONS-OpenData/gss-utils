import collections
import html
from enum import Enum
from inspect import getmro

from rdflib import RDFS, Literal, BNode, URIRef, RDF
from rdflib.term import Identifier
from typing import List

from gssutils.metadata import namespaces


class Status(Enum):
    optional = 0
    mandatory = 1
    recommended = 2


class Metadata:

    _core_properties = ['uri', '_uri', '_graph']
    _properties_metadata = {
        'label': (RDFS.label, Status.mandatory, lambda s: Literal(s, 'en')),
        'comment': (RDFS.comment, Status.mandatory, lambda s: Literal(s, 'en'))
    }

    def __init__(self):
        self._uri: Identifier = BNode()
        self._graph: Identifier = BNode()

    @property
    def uri(self):
        return str(self._uri)

    @uri.setter
    def uri(self, uri):
        self._uri = URIRef(uri)

    def get_graph(self):
        return str(self._graph)

    def set_graph(self, uri):
        self._graph = URIRef(uri)

    def __setattr__(self, name, value):
        if name in self._properties_metadata:
            self.__dict__[name] = value
        elif name in self._core_properties:
            super().__setattr__(name, value)
        else:
            raise AttributeError(f'Unknown attribute {name}')

    def get_unset(self):
        for local_name, profile in self._properties_metadata.items():
            prop, status, f = profile
            if status == Status.mandatory and local_name not in self.__dict__:
                yield local_name

    def get_property(self, p):
        obs = []
        for k in self._properties_metadata:
            prop, status, f = self._properties_metadata[k]
            if prop == p:
                obs.append(f(self.__dict__[k]))
        if len(obs) == 0:
            return None
        elif len(obs) == 1:
            return obs[0]
        else:
            return obs

    def _as_list(self, local_name: str) -> List[str]:
        return (lambda x: x if type(x) == list else [x])(self.__dict__[local_name])

    def add_to_dataset(self, dataset):
        graph = dataset.graph(self._graph)
        for c in getmro(type(self)):
            if hasattr(c, '_type'):
                if type(c._type) == tuple:
                    for t in c._type:
                        graph.add((self._uri, RDF.type, t))
                else:
                    graph.add((self._uri, RDF.type, c._type))
                break  # Only add the most specific declared type(s).
        for local_name, profile in self._properties_metadata.items():
            if local_name in self.__dict__:
                prop, status, f = profile
                v = self.__dict__[local_name]
                for obj in self._as_list(local_name):
                    graph.add((self._uri, prop, f(obj)))
                    if isinstance(obj, Metadata):
                        obj.add_to_dataset(dataset)

    def _repr_html_(self):
        s = f'<h3>{type(self).__name__}</h3>\n<dl>'
        for local_name, profile in self._properties_metadata.items():
            if local_name in self.__dict__:
                prop, status, f = profile
                s = s + f'<dt>{html.escape(prop.n3(namespaces))}</dt>'
                for obj in self._as_list(local_name):
                    term = f(obj)
                    if type(term) == URIRef:
                        s = s + f'<dd><a href={str(term)}>{html.escape(term.n3())}</a></dd>\n'
                    else:
                        s = s + f'<dd>{html.escape(term.n3())}</dd>\n'
        s = s + '</dl>'
        return s
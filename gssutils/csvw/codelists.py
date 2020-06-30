import collections
import json

from rdflib import Graph, Literal, BNode, URIRef
from rdflib.namespace import SKOS, DCTERMS, RDFS, RDF
import pandas as pd

from gssutils import *


def generate_codelist_rdf(dataset_id, df, base_url, output_path):
    """
    Given a pandas dataframe (consisting only of columns that need codelists) serialise those
    codelists and output as RDF.
    """
    
    Triple = collections.namedtuple('Triple', 's p o')
    
    for column_label in df.columns.values:
        triples = []
        
        try:
            codelist_id = pathify(column_label)
            this_codelist_concept_scheme = URIRef(f"{base_url}/def/concept-scheme/{dataset_id}/{codelist_id}")
            
            # Set title of codelist
            triples.append(Triple(
                    s=this_codelist_concept_scheme,
                    p=DCTERMS.title,
                    o=Literal(column_label)
                ))
            
            # Set type
            triples.append(Triple(
                    s=this_codelist_concept_scheme,
                    p=RDF.type,
                    o=SKOS.ConceptScheme
                ))
            
            # Set concept-scheme label
            triples.append(Triple(
                    s=this_codelist_concept_scheme,
                    p=RDFS.label,
                    o=Literal(column_label)
                ))
            
            for item in df[column_label].unique():
                
                this_code = URIRef(f"{base_url}/def/concept/{dataset_id}/{codelist_id}/{pathify(str(item))}")
                
                # Add the has top concept to outer scope
                triples.append(Triple(
                    s=this_codelist_concept_scheme,
                    p=SKOS.hasTopConcept,
                    o=this_code
                ))
                
                # Add as member of outer scope
                triples.append(Triple(
                    s=this_codelist_concept_scheme,
                    p=SKOS.member,
                    o=this_code
                ))      
                
                # currently just simple non hierarcical coelists, so EVERYTHING is the top concept
                triples.append(Triple(
                    s=this_code,
                    p=SKOS.topConceptOf,
                    o=this_codelist_concept_scheme
                ))
                
                # Label
                triples.append(Triple(
                    s=this_code,
                    p=RDFS.label,
                    o=Literal(item)
                ))
                
                # Pref label
                triples.append(Triple(
                    s=this_code,
                    p=SKOS.prefLabel,
                    o=Literal(item)
                ))

                # Notation
                triples.append(Triple(
                    s=this_code,
                    p=SKOS.notation,
                    o=Literal(pathify(item))
                ))
                
                # inSchema
                triples.append(Triple(
                    s=this_code,
                    p=SKOS.inScheme,
                    o=this_codelist_concept_scheme
                ))
                
                # is type Concept
                triples.append(Triple(
                    s=this_code,
                    p=RDF.type,
                    o=SKOS.Concept
                ))
            
            graph = Graph()
            for triple in triples:
                graph.add((triple.s, triple.p, triple.o))

            print("Generating codelist for: {}".format(column_label))
            graph.serialize("{}/{}.json".format(output_path, pathify(column_label)), format='json-ld')
        
        except Exception as e:
            raise Exception("Failed to create codelist for '{}'.".format(column_label)) from e
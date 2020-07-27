from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import OWL, VOID, DCTERMS, RDF, RDFS, SKOS, XSD, FOAF
from gssutils import pathify
from pathlib import Path

import pandas as pd
import numpy as np
import csv
import json
import os


class COGSCSVtoRDF:
    def __init__(self):
        self._codelistName = None
        self._path = None
        self._codelist = None
        self._g = None
        self._mainURI = None
        self._sortPriority = None
        self._output_path = None
        self._jsonInfo = None
        self._repoBase = None
        self._subURI = None
        self._tripleError = False
        self._language = None


    def getDatatype(self, tpe):
        if (tpe == "string"):
            return XSD.string
        elif tpe =='integer':
            return XSD.integer
        elif tpe == 'double':
            return XSD.double
        elif tpe == 'boolean':
            return XSD.boolean


    def findRDFLibType(self, tpe):
        tpe = str(tpe)
        if ("RDFS" in tpe) | ("rdfs" in tpe):
            if "label" in tpe:
                return RDFS.label
            elif "comment" in tpe:
                return RDFS.comment
        elif ("RDF" in tpe) | ("rdf" in tpe):
            if "type" in tpe:
                return RDF.type
        elif ("SKOS" in tpe) | ("skos" in tpe):
            if "notation" in tpe:
                return SKOS.notation
            elif "broader" in tpe:
                return SKOS.broader
            elif "prefLabel" in tpe:
                return SKOS.prefLabel
            elif "inScheme" in tpe:
                return SKOS.inScheme
            elif "topConceptOf" in tpe:
                return SKOS.topConceptOf
            elif "hasTopConcept" in tpe:
                return SKOS.hasTopConcept
            elif "Concept" in tpe:
                return SKOS.Concept
            elif "member" in tpe:
                return SKOS.member
        elif ("sortPriority" in tpe) | ("sortpriority" in tpe):
            return self._sortPriority
        else:
            return None


    def displayTripleErrorMessage(self, str1, str2, str3, rowNo, dat):
        print(" **************** ERROR: A REQUIRED column is missing its value, cannot form TUPLE  ****************  ")
        print("\tColumn: " + str1)
        print("\tProperty URL: " + str2)
        print("\tValue URL: " + str3)
        print("\tRow Number: " + str(rowNo))
        print("\tData: " + dat[0] + " : " + dat[1] + " : " + dat[2] + " : " + dat[3])
        print(" ******************  ******************  ******************  *******************  ****************** ")


    def initialise(self, nme, path):
        # Name of the codelist and output path
        self._codelistName = nme
        self._output_path = path + "/" + pathify(self._codelistName)
        # Open csv codelist file and read in contents
        with open(f"{self._output_path}.csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader) # Skip over column names
            self._codelist = list(csv_reader)
        csv_file.close()

        # create a Graph
        self._g = Graph()

        # Create the base RDF URI string
        self._repoBase = "http://gss-data.org.uk/def"
        self._mainURI = URIRef(f"{self._repoBase}/def/concept-scheme/{pathify(self._codelistName)}")
        # Set up the sort priority ref URI
        self._sortPriority = URIRef("http://www.w3.org/ns/ui#sortPriority")

        info = json.load(open(f'{path}/{pathify(self._codelistName)}-schema.json')) 
        self._language = info['@context'][1]['@language']
        self._jsonInfo = info['tables'][0]
        # Set the main reference URI (might need to change to @id)
        self._mainURI = URIRef(self._jsonInfo["aboutUrl"])
        self._jsonInfo = info['tables'][0]['tableSchema']
        # Set the sub reference URI (might need to change to @id)
        self._subURI = self._jsonInfo["aboutUrl"]
        self._jsonInfo = info['tables'][0]['tableSchema']['columns']
        #print(self._jsonInfo)


    def convert_To_RDF(self):
        i = 1
        for c in self._codelist:
            print(c[0])
            for l in self._jsonInfo:
                # Set up the SUBJECT, if has_top_concept or member then it needs the main URI as its subject
                if ("has_top_concept" in l["name"]) | ("member" in l["name"]):
                    subj = self._mainURI
                else:
                    subj = URIRef(self._subURI + "/" + c[1])
                    # Create a shortcut prefix for each individual codelist value, ok for small codelist but probably roo much for the big ones!
                    #self._g.bind(c[1].replace('-',''), subj) 
                # Set up the PREDICATE, always seems to be in the format @prefix:RDF Vocabulary
                pred = self.findRDFLibType(l['propertyUrl'])
                # Set up the OBJECT, this could be a URL, string or Integer. Some URLs and strings will need words replacing with the actual codelist value
                objt = self.findRDFLibType(l['valueUrl'])
                # Required is not always in scheme
                try:
                    required = l["required"]
                except:
                    required = "false"
                # If nothing has come back from the RDFLib type then its probably a URL that needs formatting or a sort priority number
                if objt is None:
                    if "label" in l["valueUrl"]:
                        if (required == True) & (len(c[0]) == 0):
                            self._tripleError = True
                            print("Its been set to true")
                        else:
                            objt = l['valueUrl'].replace('{label}',c[0])
                    elif "notation" in l["valueUrl"]:
                        if (required == True) & (len(c[1]) == 0):
                            self._tripleError = True
                        else:
                            objt = l['valueUrl'].replace('{notation}',c[1])
                    elif "parent-notation" in l["valueUrl"]:
                        if (required == True) & (len(c[2]) == 0):
                            self._tripleError = True
                        else:
                            objt = l['valueUrl'].replace('{parent-notation}',c[2])
                    elif "sort-priority" in l["valueUrl"]:
                        if (required == True) & (len(c[3]) == 0):
                            self._tripleError = True
                        else:
                            objt = l['valueUrl'].replace('{sort-priority}',c[3])
                    else:
                        objt = l["valueUrl"]

                    if self._tripleError == True:
                        self.displayTripleErrorMessage(l['name'], l['propertyUrl'], l['valueUrl'], i, c)
                        break
                # Check if the value is numerical, if it is make it numeric and then a Literal. if not check if it is a URL, if so then convert it to a URIRef. Otherwise just make it a Literal
                if objt.isnumeric():
                    objt = Literal(int(objt))
                elif "http://" in objt:
                    objt = URIRef(objt)
                else:
                    objt = Literal(objt)

                if ("{" in str(objt)) & ("}" in str(objt)):
                    objt = None

                print(str(subj) + ' - ' + str(pred) + ' - ' + str(objt))
                # Add the formatted triple to the Graph object
                if objt is not None:
                    tup = (subj, pred, objt)
                    self._g.add(tup)

            i = i + 1
            if self._tripleError == True:
                break
        print(self._tripleError)
        if self._tripleError == False:
            # Add the main codelist triples
            self._g.add((self._mainURI, DCTERMS.title, Literal(self._codelistName, lang=self._language)))
            self._g.add((self._mainURI, RDF.type, SKOS.ConceptScheme))
            self._g.add((self._mainURI, RDFS.label, Literal(self._codelistName, lang=self._language)))
            # Bind the RDF types to help with prefixes
            self._g.bind("skos", SKOS)
            self._g.bind("dcterms", DCTERMS)
            self._g.bind("rdf", RDF)
            self._g.bind("codelistURI", self._mainURI)
            # Format and output to a turtle file
            print("-")
            print("Outputting RDF in Turtle format into location: " + self._output_path + '.ttl')
            print("-")
            self._g.serialize(destination=self._output_path + '.ttl', format='turtle')
        else:
            print("Not outputting RDF due to error")


class CSVCodelists:
    def __init__(self):
        self._column_names = []

    
    def create_codelists(self, vals, path, fam, nme):
        try:
            self._column_names = list(vals)
            for c in self._column_names:
                dat = pd.DataFrame(vals[c].unique())
                dat = dat.rename(columns={0: 'Label'})
                dat['Label'] = dat['Label'].str.replace('-',' ')
                dat['Notation'] = dat['Label'].apply(pathify)
                dat['Parent Notation'] = ''
                dat['Sort Priority'] = np.arange(dat.shape[0]) + 1

                out = Path(path)
                out.mkdir(exist_ok=True)
                dat.to_csv(path + f'/{pathify(c)}.csv', index = False)
        except Exception as e:
            print('CODELIST Error: ' + str(e))

        try:
            #with open('../../Reference/codelist-template.csv-metadata.json', 'r') as schema:
            with open('gssutils/csvw/codelist-template.csv-metadata.json', 'r') as schema:
                txt = schema.read()
                schema.close()
            
            txt = txt.replace('{codelist}',pathify(c))
            txt = txt.replace('{family}',fam)
            txt = txt.replace('{transformname}',nme)
            
            
            txt = txt.replace('{codelistlabel}',c)
            f = open(path + f"/{pathify(c)}.csv-metadata.json", "w")
            f.write(txt)
            f.close()
        except Exception as e:
            print('SCHEMA Error: ' + str(e))


#df = pd.read_csv (r'gssutils/csvw/observations.csv')
#df['Location of Death'] = df['Location of Death'].str.replace("-"," ")
#df['Cause of Death'] = df['Cause of Death'].str.replace("-"," ")
#df['Location of Death'] = df['Location of Death'].str.capitalize()
#df['Cause of Death'] = df['Cause of Death'].str.capitalize()
#cl = CSVCodelists()
#df1 = pd.DataFrame(df['Location of Death'])
#cl.create_codelists(df1, 'gssutils/csvw/codelists', 'covid-19', Path(os.getcwd()).name)
#print(df1['Cause of Death'].unique())
##df1 = pd.DataFrame(df['Cause of Death'] )
#cl.create_codelists(df1, 'gssutils/csvw/codelists', 'covid-19', Path(os.getcwd()).name)

#rd = COGSCSVtoRDF()
#rd.initialise("Air Arrivals", "gssutils/csvw/out")
#rd.convert_To_RDF()

#'codelist-template.csv-metadata.json'
import pandas as pd
import numpy as np
from gssutils import pathify

class CSVCodelists:
    def __init__(self):
        self._column_names = []

    
    def create_codelists(self, vals, path):
        self._column_names = list(vals)
        for c in self._column_names:
            dat = pd.DataFrame(vals[c].unique())
            dat = dat.rename(columns={0: 'Label'})
            dat['Notation'] = dat['Label'].apply(pathify)
            dat['Parent Notation'] = ''
            dat['Sort Priority'] = np.arange(dat.shape[0]) + 1
            dat.to_csv(path / f'{pathify(c)}.csv', index = False)
            
            with open('../codelist-schema.json', 'r') as schema:
                txt = schema.read()
                schema.close()
            
            txt = txt.replace('CODELISTNAME',pathify(c))
            txt = txt.replace('CODELISTLABELNAME',c)
            
            f = open(path / f"{pathify(c)}.json", "w")
            f.write(txt)
            f.close()
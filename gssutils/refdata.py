# ###### CODE TO CREATE A SET OF REFERENCE DATA FOR A PASSED DATASET: CODELISTS IN CSV FORMAT AS WELL AS A                          ###### COLUMN.CSV AND COMPONENTS.CSV FILE

"""
These methods take the data you have transformed and creates a set of reference files from it. 
You will have had to create and defined a DataFrame that defines some parameters of the transformed data:
    1. Column heading names from transformed data
    2. For each one, if you want to create a codelist, Y/N
    3. What type of column it is, D (Dimension), M (Measure), A (Attribute)
    4. A description of the column heading for the components.csv file (OPTIONAL)
An example of the parameter DataFrame needed is shown at the bottom of this file.

To run the code you need call the create_ref_data() method and pass it:
    1. The transformed dataset (mainDat)
    2. The parameter dataset (paramDat)
    3. If you want to add a priority numbering to each codelist file, True/False (addPriority)

The create_ref_data method loops around each of the rows in the parameter dataset creating codelist, if needed 
along with column.csv and components.csv files. create_ref_data calls the other 3 methods within the loop.

    create_ref_data:
        -> create_codelist
        -> create_columns_csv_def
        -> create_components_csv_def

The create_ref_data method creates a folder called reference within your current folder path and adds the 
columns.csv and components.csv file to it. within the reference folder it creates a dataset folder and places
any codelist.csv files into it.
    current folder path/
        -> reference/
            -> columns.csv
            -> components.csv
            -> codelists/
                -> codelist1.csv 
                -> codelist2.csv 
                   Codelist file names will be the column heading passed within the parameters DataFrame
                   with any spaces replaced with a - and all lowercase
                   
When the columns.csv and components.csv files are created it treats all columns as if they have had codelists created
adding URIs where needed. It also treats the Value column this way. You will need to open the files and alter as needed.
So if you have a Column that references Sex (M|F|T) then you will need to open the file and change the data to
point to the relevent URIs. 
For instance, if you have a column called ONS Geography then it will be defined as follows
    title:                ONS Geography
    name:                 ons_geography
    component_attachment: qb:dimension
    property_template:    http://gss-data.org.uk/def/dimension/ons-geography
    value_template:       http://gss-data.org.uk/def/concept/ons-geography/{ons_geography}
    datatype:             string
    value_transformation: slugize
    regex:                {Empty}
    range:                http://gss-data.org.uk/def/classes/ons-geography/ons_geography

This would normally have to reference the statistical geography web site so some values will need to be changed to:
    property_template:    http://purl.org/linked-data/sdmx/2009/dimension#refArea
    value_template:       http://statistics.data.gov.uk/id/statistical-geography/{ons_geography}
    value_transformation: {Empty}
    regex:                [A-Z][0-9]{8}
    range:                {Empty}

The components.csv file will also need similar amendments. 
Future versions of this code will hopefully reduce the amount of changes needed to the output files.
Codelist files need to be checked for NAs, NANs or blanks

The main methods returns the number of codelist files created
"""

from gssutils.utils import pathify
from pathlib import Path
import pandas as pd

# +
def create_ref_data(mainDat, paramDat, addPriority):
    try:
        #################################################################################################
        #### Variable setup section
        refClPath = Path('reference/codelists')
        refClPath.mkdir(exist_ok=True, parents=True)
        refPath = Path('reference')
        noCodeListsCreated = 0
        #### Initialise a temporary Columns dataset, this will be overwritten in the loop
        colTbl = create_columns_csv_def('TEMP', 'TEMP', 'D')
        #### Initialse a temporary Components dataset, this will be overwritten in the loop
        comTbl = create_components_csv_def('TEMP', 'TEMP', 'D', '')

        #### Loop around each row of the Column Parameter dataset
        for i in range(0, len(paramDat)):
            ##################################################################################################
            #### Set up some variables
            columnName = paramDat.iloc[i,0]           #### Main Column Name.
            createList = paramDat.iloc[i,1]           #### Create a codelist, Y or N
            componentType = paramDat.iloc[i,2]        #### Component Type, Dimension, Attribute etc.
            descript =  paramDat.iloc[i,3]            #### Description of the Column.

            #### Assign the Component type
            if componentType == 'M':
                compTpeCapital = 'Measure'
                compTpeLower = 'measure'
            elif componentType == 'A':
                compTpeCapital = 'Attribute'
                compTpeLower = 'attribute'
            else:
                compTpeCapital = 'Dimension'
                compTpeLower = 'dimension'

            #### Slugify the column name, make lowercase and replace spaces, hyphens with underscores(_)
            #### THIS MIGHT NEED OTHER THINGS TAKEN OUT OR REPLACED AS AND WHEN FOUND
            slugColumnName = columnName.replace(' ','-').replace('_','-').lower()

            #################################################################################################
            #### This is the CODELIST section, only create if value is Y
            if createList == 'Y':
                ret = create_codelist(mainDat[columnName], columnName, slugColumnName, addPriority, refClPath)
                if ret == 'Success':
                    noCodeListsCreated = noCodeListsCreated + 1

            #################################################################################################
            #### This is the COLUMNS.CSV section, create new instance of columns during first loop and concatenate on further loops.
            #### File will need to be altered by hand to change references to external ones
            #### The Value column is created just like the others so will also need to be altered later.
            if i == 1:
                colTbl = create_columns_csv_def(columnName, slugColumnName, compTpeLower)
            else:
                colTbl = pd.concat([colTbl, create_columns_csv_def(columnName, slugColumnName, compTpeLower)])

            #################################################################################################
            #### This is the COMPONENTS section, create new instance of columns during first loop and concatenate on further loops.
            #### File will need to be altered by hand to change references to external ones
            #### All Columns are put in file so any not needed will need to be removed after
            if i == 1:
                comTbl = create_components_csv_def(columnName, slugColumnName, compTpeCapital, descript)
            else:
                comTbl = pd.concat([comTbl, create_components_csv_def(columnName, slugColumnName, compTpeCapital, descript)])

            #####################################################################################################
            #### OUT OF THE LOOP

            #### Output COLUMNS data to CSV
            colTbl.to_csv(refPath / 'columns.csv', index = False)

            #### Output COMPONENTS data to CSV
            comTbl.to_csv(refPath / 'components.csv', index = False)

        return f'{noCodeListsCreated} Codelists Created'
    except Exception as e:
        return "create_ref_data Error: " + str(e)
        
        
def create_codelist(colDat, colNme, slugColNme, addPriority, referencePath):
    try:
        #### Set up the columns headings for the file
        titles =(
            'Label',
            'Notation',
            'Parent Notation',
            'Priority'
        )
        #### Get all the unique values of the data and turn into a DataFrame
        #### WILL HAVE TO ADD SECTION REMOVING ANY NAs or NANs or BLANKS etc
        cdeLst = colDat.unique()
        cdeLst = pd.DataFrame(cdeLst)
        
        #### Create the standard codelist and output
        cdeLst.columns = [titles[0]]
        cdeLst[titles[1]] = cdeLst[titles[0]].apply(pathify) # pathified version of the column name
        cdeLst[titles[1]] = cdeLst[titles[1]].str.replace('/', '-', regex=True)
        cdeLst[titles[2]] = ''
        if addPriority:
            cdeLst[titles[3]] = cdeLst.reset_index().index + 1
        else:
            cdeLst[titles[3]] = ''
                    
        #### Output the CODELIST to CSV
        cdeLst.to_csv(referencePath / f'{slugColNme}.csv', index = False)
                        
        return 'Success'
    except Exception as e:
        return "create_codelist Error: " + str(e)
    
    
def create_columns_csv_def(colNme, slugColNme, compTpe):
    try:
        #### Create column heading definition for the columns.csv file
        colTitles = (
            'title',
            'name',
            'component_attachment',
            'property_template',
            'value_template',
            'datatype',
            'value_transformation',
            'regex',
            'range'
        )
        
        #### Create the column definition
        colOut = pd.DataFrame()
        colOut[colTitles[0]] = colNme,
        colOut[colTitles[1]] = slugColNme.replace('-','_'),
        colOut[colTitles[2]] = f'qb:{compTpe}'
        colOut[colTitles[3]] = f'http://gss-data.org.uk/def/{compTpe}/{slugColNme}'
        colOut[colTitles[4]] = 'http://gss-data.org.uk/def/concept/' + slugColNme + '/{' + slugColNme.replace('-','_') + '}'
        colOut[colTitles[5]] = 'string'
        colOut[colTitles[6]] = 'slugize'
        colOut[colTitles[7]] = ''
        colOut[colTitles[8]] = 'http://gss-data.org.uk/def/classes/' + slugColNme + '/' + slugColNme.replace('-','_')
        
        return colOut
    except Exception as e:
        return "create_columns_csv_def: " + str(e)
    
    
def create_components_csv_def(colNme, slugColNme, compTpe, desc):
    try:       
        #### Create column heading definition for the components.csv file
        colTitles = (
            'Label',
            'Description',
            'Component Type',
            'Codelist'
        )
        
        #### Create the component definition
        comOut = pd.DataFrame()
        comOut[colTitles[0]] = colNme,
        comOut[colTitles[1]] = desc,
        comOut[colTitles[2]] = compTpe
        comOut[colTitles[3]] = f'http://gss-data.org.uk/def/concept-scheme/{slugColNme}'
        
        return comOut
    except Exception as e:
        return "create_components_csv_def: " + str(e)
# -

"""
#################### EXAMPLE CODE FOR CALLING THE ABOVE METHODS ####################
#### Create a DataFrame with all the column names
cols = pd.DataFrame(list(tbl))
#### Create a list of column names to use
colNmes = ['ColumnNames','CodeList','TypeDefinition','Description']
#### This holds the Column Names
cols.columns = ['ColumnNames']
#### Add a Column to hold a Y or N value to define if a CodeList is needed
cols[colNmes[1]] = ''
cols[colNmes[1]][0] = 'Y'
cols[colNmes[1]][1] = 'N'
cols[colNmes[1]][2] = 'N'
cols[colNmes[1]][3] = 'N'
cols[colNmes[1]][4] = 'Y'
cols[colNmes[1]][5] = 'N'
cols[colNmes[1]][6] = 'Y'
cols[colNmes[1]][7] = 'N'
cols[colNmes[1]][8] = 'N'
#### Create a Column to define what type of Column it is, Dimension (D), Attribute (A), Measure (M) etc.
cols[colNmes[2]] = ''
cols[colNmes[2]][0] = 'D'
cols[colNmes[2]][1] = 'D'
cols[colNmes[2]][2] = 'D'
cols[colNmes[2]][3] = 'D'
cols[colNmes[2]][4] = 'D'
cols[colNmes[2]][5] = 'D'
cols[colNmes[2]][6] = 'D'
cols[colNmes[2]][7] = 'M'
cols[colNmes[2]][8] = 'D'
#### Create a Column to describe what the column name means, for the components.csv file. Can be left blank
cols[colNmes[3]] = ''
cols[colNmes[3]][0] = ''
cols[colNmes[3]][1] = ''
cols[colNmes[3]][2] = ''
cols[colNmes[3]][3] = ''
cols[colNmes[3]][4] = ''
cols[colNmes[3]][5] = ''
cols[colNmes[3]][6] = ''
cols[colNmes[3]][7] = ''
cols[colNmes[3]][8] = ''
#### Pass the method the data, the column info and True if you want the Sort priority added to the codelists, else False
noFls = create_ref_data(tbl, cols, True)
"""

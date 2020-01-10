# ###### CODE TO CREATE A SET OF CODELISTS IN CSV FORMAT AS WELL AS COLUMN.CSV AND COMPONENTS.CSV FILES

from gssutils.utils import pathify


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
        return "createReferenceData Error: " + str(e)
        
        
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
        cdeLst[titles[1]] = cdeLst[titles[0]].apply(pathify)
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
        return "createCodeList Error: " + str(e)
    
    
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
        return "createColumnsCSVDef: " + str(e)
    
    
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
        return "createComponentsCSVDef: " + str(e)
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
#### Create a Column to define what type a Column it is, Dimension (D), Attribute (A), Measure (M) etc.
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
cde = createReferenceData(tbl, cols, True)
"""

{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "\"\"\"\n",
    "This script creates a set of info.json files and associated folders using ONS COGS data on AirTable\n",
    "\n",
    "To access the Bases in AirTable your own personal API key needs to be passed. To get this key go your account \n",
    "overview and generate and copy the API key in the scetion labelled API. My own personal key is held in a txt file\n",
    "on my computer and has been encrypted, so the code will not be able to access the Base unless you have your\n",
    "own API key.\n",
    "\n",
    "You will also need a Table Key for each table you with to use. To access this key go to the table and click HELP\n",
    "in the top right corner and then API Documentation, a new page will open up. In the address bar copy the setion\n",
    "of the address starting with app, so the address for table 'Dataset Producer' is:\n",
    "            \n",
    "            https://airtable.com/appb66460atpZjzMq/api/docs#curl/introduction\n",
    "            \n",
    "Copy the middle section, appb66460atpZjzMq, this is the key for the table and should be used to access its \n",
    "data along with the table name.\n",
    "\n",
    "AirTable Base used:\n",
    "    COGS Dataset ETL Records\n",
    "        Tables used:\n",
    "            Source Data\n",
    "            Family\n",
    "            Dataset Producer\n",
    "            Type\n",
    "\n",
    "The table 'Source Data' holds most of the information needed but some columns hold a 'Record ID', which can be joined\n",
    "to the other tables to create a full record set\n",
    "Joins used:\n",
    "    Source Data(Producer)  ---> Dataset Producer(Record ID) ['Full Name' and 'Name' colunms used]\n",
    "    Source Data(Family)    ---> Family(Record ID) ['Name' column used]\n",
    "    Source Data(Data Type) ---> Type(Record ID) ['Name' column used]\n",
    "\n",
    "The column 'Contact details' needs to be formatted differently to others based on given names, email addresses \n",
    "and phone numbers. BAs and DEs need to agree on a format that can be used to structure the output properly\n",
    "The method: formatContactDetails() has been created for this but is not properly coded yet.\n",
    "\n",
    "The same goes for the column 'Dimensions', the method formatDimensions() had been created for this but has \n",
    "not been coded properly yet.\n",
    "\n",
    "Once all the tables are pulled in a folder called 'infoFiles' is created and then the 'Source Data' table is \n",
    "looped through and a folder and info.json file created for each row within this folder.\n",
    "Folder structure:\n",
    "    infoFiles\n",
    "        --> DfE-a-levels-and-other-16-to-18-results\n",
    "            --> info.json\n",
    "        --> HESA-higher-education-staff-data\n",
    "            --> info.json\n",
    "\n",
    "The name for each folder is created from the values in the 'Name' columns of the tables 'Dataset Producer' and \n",
    "'Source Data' (non alpha numeric characters removed and space replaced with -)\n",
    "    eg: WG-affordable-housing-provision\n",
    "\n",
    "A main_issue number is given to each info.json file based on the current value of i within the loop. When creating\n",
    "th associated issues in Github this number should match up, if not then change the number in the info.json file.\n",
    "\"\"\"\"\"\""
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "from pprint import pprint\n",
    "from airtable import Airtable\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import os\n",
    "from cryptography.fernet import Fernet\n",
    "from pathlib import Path\n",
    "from gssutils import *"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [],
   "source": [
    "def decrypt(token: bytes, key: bytes) -> bytes:\n",
    "    return Fernet(key).decrypt(token)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 18,
   "metadata": {},
   "outputs": [],
   "source": [
    "#### Pull in the encrypted keys from a text file to access AirTable bases\n",
    "i = 0\n",
    "with open('AirTableEncrypt.txt', \"r\") as input:   \n",
    "    for line in input:\n",
    "        if (i == 0):\n",
    "            key = line.strip().strip(\"\\n\")\n",
    "        elif (i == 1):\n",
    "            encryptedKey = line.strip().strip(\"\\n\")\n",
    "        i = i + 1\n",
    "\n",
    "input.close()\n",
    "\n",
    "#print('MainKey: ' + key)\n",
    "#print('Key1: ' + encryptedKey)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [],
   "source": [
    "#### All Tables are from Base COGS Dataset ETL Records\n",
    "\n",
    "#### Source Data Table \n",
    "srcTblKey = 'appb66460atpZjzMq'\n",
    "srcTblNme = 'Source Data'\n",
    "\n",
    "#### Family Table \n",
    "famTblKey = 'appb66460atpZjzMq'\n",
    "famTblNme = 'Family'\n",
    "\n",
    "#### Dataset Producer Table\n",
    "prdTblKey = 'appb66460atpZjzMq'\n",
    "prdTblNme = 'Dataset Producer'\n",
    "\n",
    "#### Data Type Table\n",
    "tpeTblKey = 'appb66460atpZjzMq'\n",
    "tpeTblNme = 'Type'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "<Airtable table:Family>\n"
     ]
    }
   ],
   "source": [
    "#### Get all the information from AirTable\n",
    "srcAirTbl = Airtable(srcTblKey, srcTblNme, api_key=str(decrypt(encryptedKey.encode(), key).decode()))\n",
    "famAirTbl = Airtable(famTblKey, famTblNme, api_key=str(decrypt(encryptedKey.encode(), key).decode()))\n",
    "prdAirTbl = Airtable(prdTblKey, prdTblNme, api_key=str(decrypt(encryptedKey.encode(), key).decode()))\n",
    "tpeAirTbl = Airtable(tpeTblKey, tpeTblNme, api_key=str(decrypt(encryptedKey.encode(), key).decode()))\n",
    "\n",
    "print(famAirTbl)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {},
   "outputs": [],
   "source": [
    "#### Get all the table data from Airtable\n",
    "srcDat = srcAirTbl.get_all()\n",
    "famDat = famAirTbl.get_all()\n",
    "prdDat = prdAirTbl.get_all()\n",
    "tpeDat = tpeAirTbl.get_all()\n",
    "\n",
    "#### Convert the table data into DataFrame format  \n",
    "srcDat = pd.DataFrame.from_records((r['fields'] for r in srcDat))\n",
    "famDat = pd.DataFrame.from_records((r['fields'] for r in famDat))\n",
    "prdDat = pd.DataFrame.from_records((r['fields'] for r in prdDat))\n",
    "tpeDat = pd.DataFrame.from_records((r['fields'] for r in tpeDat))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {},
   "outputs": [],
   "source": [
    "def getProducer(prdCde, fullOrShort):\n",
    "    try:\n",
    "        prdCde = str(prdCde).replace('[','').replace(']','').replace(\"'\",\"\")\n",
    "        retPrd = prdDat['Full Name'][prdDat['Record ID'] == prdCde].index.values.astype(int)\n",
    "        if (fullOrShort == 1):\n",
    "            retPrd = prdDat['Full Name'][retPrd[0]] + ' (' + prdDat['Name'][retPrd[0]] + ')'\n",
    "        else:\n",
    "            retPrd = prdDat['Name'][retPrd[0]]\n",
    "        return retPrd\n",
    "    except Exception as e:\n",
    "        return \"getProducer: \" + str(e)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "metadata": {},
   "outputs": [],
   "source": [
    "def getFamily(famCde):\n",
    "    try:\n",
    "        famCde = str(famCde).replace('[','').replace(']','').replace(\"'\",\"\")\n",
    "        retFam = famDat['Name'][famDat['Record ID'] == famCde].index.values.astype(int)\n",
    "        retFam = famDat['Name'][retFam[0]]\n",
    "        return retFam\n",
    "    except Exception as e:\n",
    "        return \"getFamily: \" + str(e)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {},
   "outputs": [],
   "source": [
    "def getDataType(tpeCde):\n",
    "    try:\n",
    "        i = 0\n",
    "        retPrd = ''\n",
    "        tpeCde = tpeCde.split(',')\n",
    "        for cdes in tpeCde:\n",
    "            cdes = cdes.replace('[','').replace(']','').replace(\"'\",\"\").strip()\n",
    "            indPrd = tpeDat['Name'][tpeDat['Record ID'].str.contains(cdes)].index.values.astype(int)\n",
    "            i = i + 1\n",
    "            try:\n",
    "                retPrd = retPrd + ', ' + tpeDat['Name'][indPrd[0]]\n",
    "            except:\n",
    "                retPrd = retPrd\n",
    "        return retPrd\n",
    "    except Exception as e:\n",
    "        return \"getFamily: \" + str(e)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 13,
   "metadata": {},
   "outputs": [],
   "source": [
    "def cleanTitle(mnTle):\n",
    "    try:\n",
    "        mnTle = mnTle.replace(' ','-')\n",
    "        mnTle = ''.join(e for e in mnTle if (e.isalnum()) | (e == '-'))\n",
    "        mnTle = mnTle.lower()\n",
    "        return mnTle\n",
    "    except Exception as e:\n",
    "        return \"cleanTitle: \" + str(e)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 14,
   "metadata": {},
   "outputs": [],
   "source": [
    "def formatContactDetails(colNme, cntDtls):\n",
    "    try:\n",
    "        cntsDets = cntDtls.split(',')\n",
    "        outDtls = '\\t\\t\"' + colNme + '\":\\n\\t\\t[{\\n'\n",
    "        for cnts in cntsDets:\n",
    "            cnts = ' '.join([line.strip() for line in cnts.strip().splitlines()])\n",
    "            outDtls += f'\\t\\t\\t\\t\"{cnts}\",\\n'\n",
    "        outDtls += '\\n\\t\\t}],\\n'\n",
    "        return outDtls\n",
    "    except Exception as e:\n",
    "        return 'formatContactDetails: ' + str(e)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 15,
   "metadata": {},
   "outputs": [],
   "source": [
    "def formatDimensions(dmns):\n",
    "    try:\n",
    "        return dmns\n",
    "    except Exception as e:\n",
    "        return 'formatDimensions: ' + str(e)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 16,
   "metadata": {},
   "outputs": [],
   "source": [
    "out = Path('infoFiles')\n",
    "out.mkdir(exist_ok=True, parents=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 17,
   "metadata": {},
   "outputs": [],
   "source": [
    "####\n",
    "colNmes = list(srcDat)\n",
    "i = 0\n",
    "strToUse = True\n",
    "try:\n",
    "    for label, row in srcDat.iterrows():\n",
    "        myStr = '{\\n'\n",
    "        try:\n",
    "            mainTitle = row['Name']\n",
    "            mainTitle = cleanTitle(mainTitle)\n",
    "            for cols in colNmes:\n",
    "                strToUse = True\n",
    "                myCol = cols\n",
    "                myVal = str(row[myCol])\n",
    "                if ('Producer' in myCol):\n",
    "                    mainTitle = getProducer(myVal, 2) + '-' + mainTitle\n",
    "                    myVal2 = getProducer(myVal, 1)\n",
    "                    myVal = myVal2\n",
    "                elif ('Family' in myCol):\n",
    "                    myVal = getFamily(myVal)\n",
    "                elif ('Data type' in myCol):\n",
    "                    myVal = getDataType(myVal)\n",
    "                elif ('Contact Details' in myCol):\n",
    "                    myVal = formatContactDetails(myCol, myVal)\n",
    "                    strToUse = False\n",
    "                elif ('Dimensions' in myCol):\n",
    "                    myVal = formatDimensions(myVal)\n",
    "                else:\n",
    "                    myVal = myVal\n",
    "                if (strToUse):    \n",
    "                    myVal = ' '.join([line.strip() for line in myVal.strip().splitlines()])\n",
    "                    myStr += '\\t\\t\"' + myCol + '\": \"' + myVal.replace(\"nan\",'').replace('\"','').strip('\\n') + '\",\\n'\n",
    "                else:\n",
    "                    myStr += myVal.replace(\"nan\",'')\n",
    "                #break\n",
    "            myStr += f'\\t\\t\"transform\": {{\\n\\t\\t\\t\\t\"main_issue\":{i}\\n\\t\\t}}\\n}}'\n",
    "            infoOut = Path(out / mainTitle)\n",
    "            infoOut.mkdir(exist_ok=True, parents=True)\n",
    "            with open(infoOut / f'info.json', \"w\") as output: \n",
    "                output.write(myStr)\n",
    "                output.close\n",
    "            i = i + 1\n",
    "            #break\n",
    "        except Exception as e:\n",
    "            print(f\"{i}. Inner loop Error: \" + str(e))\n",
    "except Exception as e:\n",
    "        print(f\"{i}. Outer loop Error: \" + str(e))\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 506,
   "metadata": {},
   "outputs": [],
   "source": [
    "#tpeDat"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.6"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

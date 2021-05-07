
# Predefined formatters for use with cubes related tests

def formater_cmd_gdp_example(df):
    # Rename columns to match column names required by cmd reipe
    df = df.rename(columns={
        "Industry Section Label": "UnofficialStandardIndustrialClassification",
        "Industry Section": "sic-unofficial",
        "Period": "calendar-years",
        "Reference Area": "Geography",
        "Measure Type": "GrowthRate"
        })

    # Add any additional dimension label columns
    df["Time"] = df["calendar-years"]
    df["nuts"] = df["Geography"]
    df["quarterly-index-and-growth-rate"] = df["GrowthRate"]

    # Order things to match the implicit v4 schema
    df = df[['V4_1', 'Unit','calendar-years','Time','nuts','Geography','sic-unofficial',
    'UnofficialStandardIndustrialClassification','quarterly-index-and-growth-rate','GrowthRate']]
    return df

def formater_pmd4_gdp_example(df):
    # Create interval style period
    df["Period"] = df["Period"].map(lambda x: f'year/{x}' if len(x.strip()) == 4 else f'quarter/{x}')

    # Add the explicit area urls
    df["Reference Area"] = df["Reference Area"].map(lambda x: f'http://data.europa.eu/nuts/code/{x}' if len(x.strip()) == 3 else x)
    
    # Where we're extrating the labels (for cmd) alongside the codes drop them as they're not (currently)
    # used by pmd4ß
    df = df.drop("Industry Section Label", axis=1)
    return df
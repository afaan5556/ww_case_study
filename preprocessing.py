######## Part 0: Imports and Variables ##########
import pandas as pd
import numpy as np

# Assign path of raw data to a variable
rawDataPath = 'RawData/WeWork-RED_Insights_Candidate-Case_Study_Data_August_2018_v1.xlsx'

######## Part 1: Data Import ##########

# Read each tab of raw data to a dataframe
building_df = pd.read_excel(rawDataPath, 'Building Data')
spend_df = pd.read_excel(rawDataPath, 'Spend Data')
ti_df = pd.read_excel(rawDataPath, 'TI Data')

######## Part 2: Optimization of dataframes ##########

# Function to set dtypes to category if nunique is within a specified range
def df_series_to_categories(input_df, low=int, high=int):
    for i in input_df.columns:
        if input_df[i].nunique() > low and input_df[i].nunique() < high:
            input_df[i] = input_df[i].astype('category')

# Call df_series_to_categories on each df for columns with 1 < nunique < 100
for i in [building_df, spend_df, ti_df]:
    df_series_to_categories(i, 1, 99)

# Set datetime columns to dtype datetime in the building_df
for i in ['Open Date Per Floor', 'Possession Date', 'Lease Date']:
    building_df[i] = pd.to_datetime(building_df[i], errors='coerce')

# Set datetime columns to dtype datetime in the ti_df
ti_df['Last Presentation Date'] = pd.to_datetime(ti_df['Last Presentation Date'], errors='coerce')

######## Part 3: Drop un-needed and add needed and join-helper columns to df's ##########

# The first 36 characters of the ti_df 'Deal Code' matches the building_df 'Deal Id'
ti_df['Deal Code Id'] = ti_df['Deal Code'].map(lambda x: x[0:36])

# Use CUR and FX in Spend Data to get single USD capital expenditure that has a name consistent with the brief
spend_df['Capital Expenditure'] = spend_df['FX'] * spend_df['Sum of Spend']

# Case study is interested only in 2016 and 2017 open dates - drop other rows
building_df = building_df[building_df['Open Date Per Floor'] < '1/1/2018']
building_df = building_df[building_df['Open Date Per Floor'] > '12/31/2015']

# Remove columns that are not of interest per the case study
building_df = building_df.drop(columns=['Property Short Code', 'Owner', 'Real Estate Lead', 'Director', 'Development PM', 'Architecture Lead', 'Design Lead', 'Construction Lead', 'Floor Number', 'Floor Description', 'RSF per Floor', 'Possession Date', 'Lease Date', 'Deal Status'])

######## Part 4: Prepare df's for Joining ##########

# Create a multi-index df to prepare for collapsing into single row per property
collapsed_building_df = building_df.set_index(['Property Name', 'Market'])

# Create df that collapses the USF and desks for each property by summing them
collapsed_usf_desks = collapsed_building_df.groupby(level=[0]).sum()

# Reset index on collpased_usf_desks to allow for joining
collapsed_usf_desks.reset_index(inplace=True)

# Update column names in collapsed_usf_desks to reflect they are totals (not per floor data)
collapsed_usf_desks.rename(index=str, columns={"USF per Floor": "USF", "Desk Count per Floor": "Desk Count"}, inplace=True)

# Drop the USF and Desk columns from building_df since they are aggregated in collapsed_usf_desks
building_df.drop(['USF per Floor', 'Desk Count per Floor'], axis=1, inplace=True)

# Fill building_df using pad/forward-fill to fill blanks in the 'Project Id' column
building_df.fillna(method='pad', inplace=True)

# Drop duplicate property rows in building_df. Keep the last record to avoid pad/ffills that span multiple properties
building_df.drop_duplicates(subset='Property Name', keep='last', inplace=True)

# Merge building_df with collapsed_usf_desks to get the final building_df ready for joining
building_df = pd.merge(building_df, collapsed_usf_desks, on='Property Name', how='inner')

# Create the 'Open Year' column which is what is needed per the brief (not a per floor open date)
building_df['Open Year'] = building_df['Open Date Per Floor'].apply(lambda x: x.year)

# Drop the 'Open Date Per Floor' column which was inaccurate, temporary, and not needed per the brief
building_df.drop(columns=['Open Date Per Floor'], axis=1, inplace=True)

# Change foreign key columns to have matching names across df's to enable joining
spend_df.rename(index=str, columns={"Project Code": "Project Id"}, inplace=True)

# ti_df.rename(index=str, columns={"Deal Code Id": "Deal Id"}, inplace=True) << THIS JOIN OPTION NOT CHOSEN
# Also rename the 'TI USD' column to have a name consistent with the brief
ti_df.rename(index=str, columns={"Deal UUID": "Deal Id", "TI USD": "TI Monies Received"}, inplace=True)

########## Part 5: Join df's ##########

# Join 1: building and spend
building_spend_df = pd.merge(building_df, spend_df[['Project Id', 'Capital Expenditure']], on='Project Id', how='inner')

# Join 2: building and ti
building_ti_df = pd.merge(building_df, ti_df[['Deal Id', 'TI Monies Received']], on='Deal Id', how='inner')

# Join 3: join of joins
combined_data_source = pd.merge(building_spend_df, building_ti_df[['Deal Id', 'TI Monies Received']], on='Deal Id', how='inner')

######## Part 6: Calculate Additional Needed Data ########

# 1. Net Capital Expenditure (NCE)
combined_data_source['NCE'] = combined_data_source['Capital Expenditure'] - combined_data_source['TI Monies Received']

# 2. NCE per desk
combined_data_source['NCE per Desk'] = combined_data_source['NCE'] / combined_data_source['Desk Count']

# 3. NCE per USF
combined_data_source['NCE per USF'] = combined_data_source['NCE'] / combined_data_source['USF']

######## Part 7: Create the final combined data source ########

# Drop rows that have +infinity or -infinity NCE data
combined_data_source.dropna(subset=['NCE per Desk', 'NCE per USF'], how='all', )

# Remove +infinity and -infinity NCE data
combined_data_source.replace([np.inf, -np.inf], np.nan, inplace=True)
combined_data_source = combined_data_source.dropna(axis=0, how='any')

# Round and remove decimals on NCE data
combined_data_source['NCE per USF'] = combined_data_source['NCE per USF'].apply(lambda x: int(round(x,0)))
combined_data_source['NCE per Desk'] = combined_data_source['NCE per Desk'].apply(lambda x: int(round(x,0)))

# Set the Property Name as the index for visualization purposes
combined_data_source.set_index('Property Name', inplace=True)

# Drop outliers as seen on initial visualization << LEFT THESE IN AND INCLUDED AN OUTLIER ANALYSIS AT END
#combined_data_source.drop(index=['Property 393', 'Property 768'], axis=0, inplace=True)

# export final df to csv
combined_data_source.to_csv('combined_data_source.csv')
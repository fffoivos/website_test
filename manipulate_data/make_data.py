import pandas as pd
import re

# Define file paths
csv_file_path = '/home/fivos/Projects/GlossAPI/glossAPI/data/data_for_bert.csv'
dat_file_path = '/home/fivos/Projects/GlossAPI/glossAPI/data/annot_data_raw.dat'

# Read the CSV file
df_csv = pd.read_csv(csv_file_path)

# Read the DAT file (assuming it is tab-separated; change delimiter if needed)
df_dat = pd.read_csv(dat_file_path, delimiter='\t')

# Function to clean and standardize column names
def clean_column_names(df):
    df.columns = [col.strip() for col in df.columns]
    return df

# Clean column names
df_csv = clean_column_names(df_csv)
df_dat = clean_column_names(df_dat)

# Concatenate DataFrames column-wise
df_combined = pd.concat([df_csv, df_dat], axis=1)

# Display the combined DataFrame
print(df_combined)

# Optionally, save the combined DataFrame to a new file
df_combined.to_csv('/home/fivos/Projects/GlossAPI/glossAPI/data/text_and_annotation.csv', index=False)

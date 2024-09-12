import pandas as pd

# Read the first CSV file
df1 = pd.read_csv('/home/fivos/Downloads/trapeza_8ematon_nea2.csv', sep=',', engine='python')

# Read the second CSV file
df2 = pd.read_csv('/home/fivos/Downloads/dataset_Sep_5.csv', sep=',', engine='python')

# Merge the two dataframes based on the specified columns
combined_df = pd.merge(df1, df2, on=['text', 'Ποικιλία', 'archaia_or_not'], how='outer')

# Save the combined dataframe to a new CSV file
combined_df.to_csv('/home/fivos/Downloads/dataset_Sep_3.csv', index=False)

print("Files combined successfully!")

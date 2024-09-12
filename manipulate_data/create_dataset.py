import pandas as pd

# Read the first CSV file
df1 = pd.read_csv('/home/fivos/Downloads/trapeza_8ematon_nea2.csv', sep=',', engine='python')

# Read the second CSV file
df2 = pd.read_csv('/home/fivos/Downloads/dataset_Sep_5.csv', sep=',', engine='python')
# Step 1: Mark the first 300 rows as 'used' with 1, and the rest as 0
df1['used'] = 0
df1.loc[:299, 'used'] = 1  # Mark the first 300 rows

# Fill missing values in df1 with 1
df1 = df1.fillna(1)

# Ensure 'Ποικιλία', 'archaia_or_not', and 'used' columns are integers
df1['Ποικιλία'] = df1['Ποικιλία'].astype(int)
df1['archaia_or_not'] = df1['archaia_or_not'].astype(int)
df1['used'] = df1['used'].astype(int)

# Step 2: Select the first 300 rows from df1, excluding the 'used' column
first_300_rows = df1.head(300).drop(columns=['used'])

# Step 3: Merge the first 300 rows of df1 (without 'used' column) with df2
combined_df = pd.merge(first_300_rows, df2, on=['text', 'Ποικιλία', 'archaia_or_not'], how='outer')

# Step 4: Save the modified df1 (with the 'used' column)
df1.to_csv('/home/fivos/Downloads/trapeza_8ematon_nea2.csv', index=False)

# Step 5: Save the combined dataframe to a new CSV file (without the 'used' column)
combined_df.to_csv('/home/fivos/Downloads/dataset_Sep_9.csv', index=False)
print(df2.shape[0], combined_df.shape[0])
print("Files combined successfully without the 'used' column in the combined dataset!")

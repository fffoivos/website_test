import pandas as pd

# Read the cleaned CSV files
df1 = pd.read_csv('/home/fivos/Desktop/GlossAPI_data/cleaned_draw2text_predicted.csv', sep=',', engine='python')
df2 = pd.read_csv('/home/fivos/Desktop/GlossAPI_data/cleaned_draw3text_predicted.csv', sep=',', engine='python')

# Read the original CSV files
df1_original = pd.read_csv('/home/fivos/Desktop/GlossAPI_data/draw2texts.csv', sep=',', engine='python')
df2_original = pd.read_csv('/home/fivos/Desktop/GlossAPI_data/draw3texts.csv', sep=',', engine='python')

# Select the required columns from cleaned files
df1_selected = df1[['text', '1', '2', '3', '4','5']]
df2_selected = df2[['text', '1', '2', '3', '4','5']]

# Add the 'ΠΟΙΚΙΛΙΑ' column from original files
df1_selected['ΠΟΙΚΙΛΙΑ'] = df1_original['ΠΟΙΚΙΛΙΑ']
df2_selected['ΠΟΙΚΙΛΙΑ'] = df2_original['ΠΟΙΚΙΛΙΑ']

# Concatenate the two dataframes
combined_df = pd.concat([df1_selected, df2_selected], ignore_index=True)

# Save the combined dataframe to a new CSV file
combined_df.to_csv('/home/fivos/Desktop/GlossAPI_data/combined_draw_with_variety.csv', index=False, sep=',')

print("Files combined successfully!")

# Display the first few rows of the combined dataframe
print(combined_df.head())

# Display information about the combined dataframe
print(combined_df.info())
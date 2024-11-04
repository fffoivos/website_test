import pandas as pd

# Read the combined CSV file
df = pd.read_csv('/home/fivos/Desktop/GlossAPI_data/combined_draw_with_variety.csv', sep=',', engine='python')

# Define a mapping dictionary for normalization
variety_mapping = {
    'ΔΗΜΟΤΙΚΗ': 'Δημοτική',
    'δημοτική': 'Δημοτική',
    'ΚΑΘΑΡΕΥΟΥΣΑ': 'Καθαρεύουσα',
    'καθαρεύουσα': 'Καθαρεύουσα',
    'ΚΝΕ': 'ΚΝΕ'
}

# Apply the mapping to normalize the 'ΠΟΙΚΙΛΙΑ' column
df['ΠΟΙΚΙΛΙΑ_NORMALIZED'] = df['ΠΟΙΚΙΛΙΑ'].map(variety_mapping)

# Create a set of unique normalized varieties
unique_normalized_varieties = set(df['ΠΟΙΚΙΛΙΑ_NORMALIZED'])

# Print the set of unique normalized varieties
print("Unique normalized varieties:")
for variety in sorted(unique_normalized_varieties):
    print(variety)

# Print the total count of unique normalized varieties
print(f"\nTotal number of unique normalized varieties: {len(unique_normalized_varieties)}")

# Save the updated dataframe with the new normalized column
df.to_csv('/home/fivos/Desktop/GlossAPI_data/combined_draw_with_normalized_variety.csv', index=False, sep=',')

# Print a sample of the dataframe to verify the changes
print("\nSample of the updated dataframe:")
print(df[['ΠΟΙΚΙΛΙΑ', 'ΠΟΙΚΙΛΙΑ_NORMALIZED']].head(10))

# Print value counts of the normalized varieties
print("\nValue counts of normalized varieties:")
print(df['ΠΟΙΚΙΛΙΑ_NORMALIZED'].value_counts())
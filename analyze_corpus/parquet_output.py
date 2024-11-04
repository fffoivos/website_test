import pandas as pd

# Read the Parquet file
df = pd.read_parquet('/home/fivos/Desktop/text_sources/greek_pd_1.parquet')

# Ensure the 'text' column exists
if 'text' in df.columns:
    # Iterate over the first 10 rows
    for index, row in df.head(10).iterrows():
        text = row['text']
        print(f"--- Entry {index + 1} ---")
        # Split the text into lines and get the first 10
        lines = text.split('\n')[:10]
        # Print the first 10 lines
        print('\n'.join(lines))
        print('\n')
else:
    print("The 'text' column does not exist in the DataFrame.")

import pandas as pd
import os
import shutil

# Read and filter the CSV
df = pd.read_csv('/home/fivos/Desktop/GlossAPI_tools/scraping/gutenberg/gutenberg_output/gutenberg_metadata.csv')
print("Before filtering:")
print(df)
print("\nShape:", df.shape)

df_unique = df[~df.duplicated(subset=['author', 'title'], keep="first")]
print("\nAfter filtering (only unique author-title combinations):")
print(df_unique)
print("\nShape:", df_unique.shape)

# Create unique folder if it doesn't exist
source_path = '/home/fivos/Desktop/GlossAPI_tools/scraping/gutenberg/gutenberg_output/texts'
dest_path = os.path.join(source_path, 'unique')
os.makedirs(dest_path, exist_ok=True)

# Get list of all txt files
txt_files = [f for f in os.listdir(source_path) if f.endswith('.txt')]

# Copy matching files
copied_count = 0
for filename in txt_files:
    if filename in df_unique['text_filename'].values:
        shutil.copy2(
            os.path.join(source_path, filename),
            os.path.join(dest_path, filename)
        )
        copied_count += 1

print(f"\nCopied {copied_count} files to {dest_path}")
import pandas as pd
import numpy as np

# Read the parquet file
df = pd.read_parquet('works_extractor_async_v5.parquet')

# Analyze missing values in text column
total_rows = len(df)
missing_text = df['text'].isna().sum()
missing_text_percent = (missing_text / total_rows) * 100

print("\nAnalysis of missing values in 'text' column:")
print(f"Total rows: {total_rows}")
print(f"Missing text values: {missing_text}")
print(f"Percentage of missing text: {missing_text_percent:.2f}%")

# Analyze authors
missing_authors = df['author'].isna().sum()
missing_authors_percent = (missing_authors / total_rows) * 100

print("\nAnalysis of authors:")
print(f"Missing authors: {missing_authors}")
print(f"Percentage of missing authors: {missing_authors_percent:.2f}%")

# Get distribution of non-null authors
if 'author' in df.columns:
    print("\nTop 10 most common authors:")
    print(df['author'].value_counts().head(10))

# Analyze entries with missing authors
print("\nAnalyzing entries with missing authors:")
missing_authors_df = df[df['author'].isna()]

# Get some statistics about text length for entries with missing authors
missing_authors_df['text_length'] = missing_authors_df['text'].str.len()
print(f"\nText length statistics for entries with missing authors:")
print(missing_authors_df['text_length'].describe())

# Look at some sample titles of works with missing authors
print("\nSample titles of works with missing authors:")
print(missing_authors_df['title'].head(10))

# Get the first few words of some texts with missing authors
print("\nFirst 100 characters of some texts with missing authors:")
for idx, row in missing_authors_df.head(5).iterrows():
    print(f"\nTitle: {row['title']}")
    if isinstance(row['text'], str):
        print(f"Text preview: {row['text'][:100]}...")
    else:
        print("Text is missing")

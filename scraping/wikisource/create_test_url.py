import pandas as pd

# Read the original parquet file
df = pd.read_parquet('wikisource_urls.parquet')

# Define target URLs
target_urls = [
    'https://el.wikisource.org/wiki/%CE%A0%CE%B5%CF%81%CE%AF_%CE%B6%CF%8E%CF%89%CE%BD_%CE%B9%CE%B4%CE%B9%CF%8C%CF%84%CE%B7%CF%84%CE%BF%CF%82',
    'https://el.wikisource.org/wiki/%CE%91%CE%B9%CF%83%CF%8E%CF%80%CE%BF%CF%85_%CE%9C%CF%8D%CE%B8%CE%BF%CE%B9'
]

# Get rows for target URLs
selected_rows = df[df['url'].isin(target_urls)]

# Save to new parquet
selected_rows.to_parquet('test_urls.parquet')

print(f"Created test_urls.parquet with {len(selected_rows)} URLs:")

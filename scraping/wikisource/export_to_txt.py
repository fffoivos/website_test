import pandas as pd
import os
import re
import unicodedata
from pathlib import Path

def normalize_filename(text):
    if pd.isna(text) or text == '' or len(str(text).strip()) == 0:
        return 'unknown'
    
    # Convert to lowercase first
    text = str(text).lower()
    
    # Greek to Latin character mapping
    greek_to_latin = {
        'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i',
        'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x',
        'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y',
        'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
        'ά': 'a', 'έ': 'e', 'ή': 'i', 'ί': 'i', 'ό': 'o', 'ύ': 'y', 'ώ': 'o',
        'ϊ': 'i', 'ϋ': 'y', 'ΐ': 'i', 'ΰ': 'y'
    }
    
    # Replace Greek characters
    for greek, latin in greek_to_latin.items():
        text = text.replace(greek, latin)
    
    # Convert remaining accented characters to ASCII
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove all special characters and punctuation, replace spaces with underscore
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', '_', text)
    
    # Remove multiple underscores and trim
    text = re.sub(r'_+', '_', text)
    text = text.strip('_')
    
    # Handle empty or too short results
    if not text or len(text) < 2:
        return 'unknown'
    
    # Limit length (leaving room for potential numbers to be added)
    return text[:50]

def create_unique_filename(author, title, idx):
    # Create base filename from author and title
    base = f"{normalize_filename(author)}_{normalize_filename(title)}"
    
    # Always append the index to ensure uniqueness
    return f"{base}_{idx}"

def export_to_txt_files():
    # Create output directory
    output_dir = Path('/home/fivos/Desktop/GlossAPI_tools/scraping/wikisource/analysis/txt_exports')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read parquet file
    df = pd.read_parquet('/home/fivos/Desktop/GlossAPI_tools/scraping/wikisource/wikisource_greek.parquet')
    print(f"Total rows in parquet file: {len(df)}")
    print(f"Unique authors: {df['author'].nunique()}")
    print(f"Unique titles: {df['title'].nunique()}")
    
    # Fill NaN values
    df['author'] = df['author'].fillna('unknown_author')
    df['title'] = df['title'].fillna('unknown_title')
    df['url'] = df['url'].fillna('no_url_available')
    df['text'] = df['text'].fillna('No text available')
    df['author_year'] = df['author_year'].fillna('unknown_year')
    
    # Generate unique filenames using row index
    df['filename'] = df.apply(
        lambda x: create_unique_filename(x['author'], x['title'], x.name), 
        axis=1
    )
    
    # First, clean the output directory
    for file in output_dir.glob('*.txt'):
        file.unlink()
    
    # Export files
    files_written = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            file_path = output_dir / f"{row['filename']}.txt"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write metadata header
                f.write(f"Title: {row['title']}\n")
                f.write(f"Author: {row['author']}\n")
                f.write(f"Year: {row['author_year']}\n")
                f.write(f"URL: {row['url']}\n")
                f.write("\n" + "="*50 + "\n\n")  # Separator
                
                # Write main text
                f.write(row['text'])
            files_written += 1
            
            if files_written % 500 == 0:
                print(f"Written {files_written} files...")
        except Exception as e:
            print(f"Error processing row {idx}: {str(e)}")
            print(f"Filename attempted: {row['filename']}")
            print(f"Title: {row['title']}")
            print(f"Author: {row['author']}")
            errors += 1
    
    print(f"Total files written: {files_written}")
    print(f"Total errors: {errors}")
    
    # Verify file count
    actual_files = len(list(output_dir.glob('*.txt')))
    print(f"Actual files in directory: {actual_files}")
    if actual_files != len(df):
        print(f"Warning: Number of files ({actual_files}) doesn't match number of rows ({len(df)})")

if __name__ == "__main__":
    export_to_txt_files()

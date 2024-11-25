import os
import pandas as pd
import glob
from typing import Dict, List

def read_text_file(file_path: str) -> str:
    """Read text content from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_texts_dataset(cleaned_files_dir: str, metadata_path: str) -> pd.DataFrame:
    """
    Create a dataset from cleaned text files and metadata.
    
    Args:
        cleaned_files_dir: Path to directory containing cleaned text files
        metadata_path: Path to CSV file containing metadata with author, title, filename columns
    
    Returns:
        DataFrame with author, title, and text columns
    """
    # Read metadata
    metadata_df = pd.read_csv(metadata_path)
    
    # Initialize lists to store data
    texts_data: List[Dict[str, str]] = []
    
    # Process each text file
    for txt_file in glob.glob(os.path.join(cleaned_files_dir, "*.txt")):
        # Get filename without extension
        base_filename = os.path.splitext(os.path.basename(txt_file))[0]
        
        # Create XML filename for matching
        xml_filename = f"{base_filename}.xml"
        
        # Find matching metadata row
        metadata_row = metadata_df[metadata_df['filename'] == xml_filename]
        
        if not metadata_row.empty:
            # Read text content
            text_content = read_text_file(txt_file)
            
            # Add to dataset
            texts_data.append({
                'author': metadata_row['author'].iloc[0],
                'title': metadata_row['title'].iloc[0],
                'text': text_content
            })
        else:
            print(f"Warning: No metadata found for {xml_filename}")
    
    # Create DataFrame
    return pd.DataFrame(texts_data)

def main():
    # Configuration
    cleaned_files_dir = "/home/fivos/Desktop/First1KGreek_fork/1k_extracted_text_8v/cleaned_files/"  # Directory containing cleaned text files
    metadata_path = "/home/fivos/Desktop/First1KGreek_fork/1k_metadata.csv"  # Path to metadata CSV file
    output_file = "/home/fivos/Desktop/First1KGreek_fork/1k_texts.parquet"  # Output parquet file name
    
    print(f"Reading cleaned files from: {cleaned_files_dir}")
    print(f"Reading metadata from: {metadata_path}")
    
    # Create dataset
    df = create_texts_dataset(cleaned_files_dir, metadata_path)
    
    # Save to parquet
    df.to_parquet(output_file)
    print(f"\nDataset created successfully!")
    print(f"Total texts processed: {len(df)}")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()

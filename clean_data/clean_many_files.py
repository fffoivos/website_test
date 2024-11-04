import pandas as pd
import re
import os
from transformers import AutoTokenizer
from glob import glob

# Import the functions from the specified file
import sys
sys.path.append('/home/fivos/Projects/GlossAPI/clean_code/')
from clean_data_with_mask import clean_text, is_mostly_latin, is_mostly_numbers, too_short, has_more_than_512_tokens

# Set the directory containing the CSV files
input_dir = "/home/fivos/Projects/GlossAPI/test_data/"

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained("nlpaueb/bert-base-greek-uncased-v1")

# Get all CSV files in the directory
csv_files = glob(os.path.join(input_dir, "*.csv"))

# Process each file
for file_path in csv_files:
    # Load the data
    data = pd.read_csv(file_path, sep=",", engine="python")

    print(f"Processing {file_path}...")

    # Ensure 'text' column contains strings
    if 'text' in data.columns:
        data["text"] = data["text"].astype(str)
    else:
        print(f"Column 'text' not found in {file_path}. Skipping this file.")
        continue

    # Create the mask column
    data['mask'] = 1

    # Update mask for empty text cells
    data.loc[~data["text"].str.strip().astype(bool), 'mask'] = 0

    # Update mask for mostly Latin text
    data.loc[data["text"].apply(is_mostly_latin), 'mask'] = 0

    # Update mask for mostly numbers
    data.loc[data["text"].apply(is_mostly_numbers), 'mask'] = 0

    # Update mask for too_short text
    data.loc[data["text"].apply(too_short), 'mask'] = 0

    # Apply the cleaning function to all rows
    data["text"] = data["text"].apply(clean_text)

    # Strip trailing whitespaces
    data["text"] = data["text"].apply(str.strip)

    # Update mask for text with more than 512 tokens
    data.loc[data["text"].apply(has_more_than_512_tokens), 'mask'] = 0

    # Save the result to a new CSV file
    output_path = os.path.join(input_dir, f"masked_{os.path.basename(file_path)}")
    data.to_csv(output_path, index=False, quoting=1)  # quoting=1 ensures all fields are quoted

    print(f"Cleaned data with mask saved to {output_path}")

print("All files processed.")

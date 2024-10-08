import os
import csv
import pandas as pd
import re
from collections import Counter

def is_uppercase_greek(text):
    # Split the text by spaces
    words = text.split()
    if not words:
        return []

    # Regular expression pattern to match Greek UPPERCASE letters and not lower case
    greek_uppercase_pattern = r'^((?!.*→α-ωά-ώ)[Α-ΩΆ-Ώ\d:\- ]+)$'

    # Collect all fully uppercase Greek words until a non-uppercase word is found
    uppercase_greek_words = []
    for word in words:
        if ( word.isupper() and re.match(greek_uppercase_pattern, word) ) or word in ["-", ":"] or word.isdigit():
            uppercase_greek_words.append(word)
        else:
            break
    
    for word in uppercase_greek_words:
        if word == "→":
            return []
        if len(word) > 1 and not word.isdigit():
            return uppercase_greek_words
    
    return []

def process_csv_file(input_file, output_folder):
    print(f"Processing file: {os.path.basename(input_file)}")
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Add new column for removed page headings
    df['Removed page heading'] = ''
    
    # Initialize variables
    current_page = df['page'].iloc[0]
    rows_to_remove = []
    
    # Iterate through the dataframe
    for i in range(1, len(df)):
        if df['page'].iloc[i] > current_page:
            # Page change detected
            start_index = i
            end_index = None
            
            # Search for the first UP == 1 within the next 6 rows
            for j in range(i, min(i + 6, len(df))):
                if df['UP'].iloc[j] == 1:
                    end_index = j
                    break
            
            if end_index is not None:
                # Extract and store the header text
                header_text = ' '.join(df['text'].iloc[start_index:end_index])
                df.at[start_index, 'Removed page heading'] = header_text
                
                # Mark rows for removal
                rows_to_remove.extend(range(start_index, end_index))
            
            # Update current page
            current_page = df['page'].iloc[i]
    
    # Remove marked rows
    df = df.drop(rows_to_remove)
    
    # Reset index
    df = df.reset_index(drop=True)
    
    # Write the new dataframe to a CSV file
    output_file = os.path.join(output_folder, os.path.basename(input_file).replace('.csv', '_processed.csv'))
    df.to_csv(output_file, index=False)

def process_csv_files(input_folder):
    # Create the output folder
    output_folder = os.path.join(input_folder, "test")
    os.makedirs(output_folder, exist_ok=True)
    
    # Iterate over all CSV files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.csv'):
            input_file = os.path.join(input_folder, filename)
            process_csv_file(input_file, output_folder)

# Usage
input_folder = '/home/fivos/Desktop/New Folder/Sxolika/filtered_by_JSON/cleaned_filtered_extracted_txt/fine_cleaning_v2/extracted_pages/'
process_csv_files(input_folder)
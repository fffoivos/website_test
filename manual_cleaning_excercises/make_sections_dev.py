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
    
    # Initialize an empty list to store our new rows
    new_rows = []
    
    # Keep track of the last index
    last_index = 0
    
    # Iterate over each row in the dataframe
    for _, row in df.iterrows():
        page = row['page']
        text = row['text']
        
        # Split the text into segments
        segments = text.split('\n')
        # Add each segment as a new row
        for segment in segments:
            cleaned_segment = re.sub(r'\s+', ' ', segment.strip())
            #if segment.strip():  # Only add non-empty segments
            upper_case_greek = is_uppercase_greek(cleaned_segment)
            new_rows.append({
                'index': last_index + 1,
                'text': cleaned_segment,
                'page': page,
                'UP': 1 if upper_case_greek else 0,
                'heading': " ".join(upper_case_greek) if upper_case_greek else ''
            })
            last_index += 1
    
    # Create a new dataframe from our list of rows
    new_df = pd.DataFrame(new_rows)
    
    # Count the occurrences of each text
    text_counts = Counter(new_df['text'])
    new_df['repeats'] = new_df['text'].apply(lambda x: x if text_counts[x] > 5 else '')
    
    # Write the new dataframe to a CSV file
    output_file = os.path.join(output_folder, os.path.basename(input_file).replace('.csv', '_sections.csv'))
    new_df.to_csv(output_file, index=False)

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
input_folder = '/home/fivos/Desktop/cleaned_filtered_extracted_txt/fine_cleaning/extracted_pages'
process_csv_files(input_folder)
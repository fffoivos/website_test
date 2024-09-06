import csv
import re
import unicodedata
import os

def is_mostly_greek(text):
    greek_chars = sum(1 for char in text if unicodedata.name(char, '').startswith('GREEK'))
    total_chars = len(text)
    return greek_chars / total_chars > 0.5 if total_chars > 0 else False

def clean_text(text):
    # Remove leading/trailing spaces
    text = text.strip()
    
    # Remove special characters except parentheses and punctuation
    text = re.sub(r'[^\w\s().,;:!?"-]', '', text)
    
    # Remove enumeration elements
    text = re.sub(r'^\s*(?:\d+[).:]|\(\d+\))\s*', '', text)
    
    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text

def process_file(working_dir, input_file, output_file):
    input_path = os.path.join(working_dir, input_file)
    output_path = os.path.join(working_dir, output_file)

    with open(input_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=['text'])
        writer.writeheader()

        for row in reader:
            text = row['text']
            if text:  # Skip empty cells
                cleaned_text = clean_text(text)
                if cleaned_text and is_mostly_greek(cleaned_text):
                    writer.writerow({'text': cleaned_text})

    print(f"Cleaned data has been written to {output_path}")
    
# Specify your working directory, input file name, and output file name
working_directory = '/home/fivos/Desktop/clean_code/'  # Replace this with your actual working directory
input_file_name = 'validation_draw2texts.csv'
output_file_name = 'cleaned_draw2texts.csv'

# Call the function to process the file
process_file(working_directory, input_file_name, output_file_name)
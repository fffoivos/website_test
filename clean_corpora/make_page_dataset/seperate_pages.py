import os
import re
import unicodedata
import pandas as pd

# Define the directory paths
input_directory = '/home/fivos/Projects/GlossAPI/manual_cleaning_excercises/check_papers/1-50'
# Outputs here:
output_directory = os.path.join(input_directory, 'cleaning_algo_presentation1-50_v3')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Intended match: Greek_words, optional space, more than 3 dots, optional space and/or "σελ.", finally a number and nothing else concatenated to it.
#   eg 'ΠΡΟΚΑΤΑΡΚΤΙΚΕΣ ΕΡΓΑΣΙΕΣ ΣΥΝΤΗΡΗΣΗΣ ........................................................50'
index_pattern = re.compile(r"([α-ωΑ-Ωά-ώ\d:]+)\s{0,2}(?:[.ο•]{4,}|(?:[.ο•]+\s{1,2})+[.ο•]+)(\s{0,2}σελ\.)?\s{0,2}\d+(?!\S)")

# Pattern for bibliography
bibliography_pattern = re.compile(r".*βιβλιογραφια.*")

def process_file(file_path):
    last_index_line_number = 0
    bibliography_line_number = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        # Set bibliography_line_number to last line number by default
        txt_length = len(lines)
        bibliography_line_number = len(lines)
        
        for line_number, line in enumerate(lines, 1):
            # Check for index entries
            if (line_number/txt_length) < 0.5 and index_pattern.search(line):
                last_index_line_number = line_number
            
            # Check for bibliography
            if (line_number/txt_length) > 0.5 and find_bibliography_line(line):
                bibliography_line_number = line_number - 1
                break  # Stop processing after finding bibliography
    
    return last_index_line_number, bibliography_line_number, lines

def find_bibliography_line(line):
    # Removes combined characters ie accents from Greek letters
    accentless_line = ''.join(c for c in unicodedata.normalize('NFD', line) if unicodedata.category(c) != 'Mn')
    # Remove any non-printable characters and collapse whitespace
    concat_line = re.sub(r'[^α-ωΑ-Ω]', '', accentless_line)  # Keeps only Greek characters
    if len(concat_line) < 40:
        match = bibliography_pattern.match(concat_line.lower())
        return match
    else:
        return False

def main():
    # Process each file in the input directory
    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        
        # Skip directories and non-text files
        if os.path.isdir(file_path) or not filename.endswith('.txt'):
            continue
        
        # Process the file
        print(f"Processing {filename}")
        last_index_line_number, bibliography_line_number, lines = process_file(file_path)
        
        # Prepare output data array
        data = []
        inside_content = False
        first_10_in = []
        first_10_out = []
        for line_number, line in enumerate(lines, 1):
            if line_number == last_index_line_number + 1:
                # Start of content
                inside_content = True
            if line_number == bibliography_line_number + 1:
                # End of content
                inside_content = False
            
            # Determine the status of the line (whether inside or outside the content)
            status = 'IN' if inside_content else 'OUT'
            
            # Store line data in a list
            data.append({
                'page_num': line_number,
                'text': line.strip(),
                'status': status
            })

            # Collect the first 10 "IN" and "OUT" lines
            if status == 'IN' and len(first_10_in) < 10:
                first_10_in.append((line_number, line.strip()))
            if status == 'OUT' and len(first_10_out) < 10:
                first_10_out.append((line_number, line.strip()))

        # Display the first 10 lines that are "IN"
        if first_10_in:
            print(f"\nFirst 10 'IN' lines for {filename}:")
            for num, content in first_10_in:
                print(f"{num}: {content}")

        # Display the first 10 lines that are "OUT"
        if first_10_out:
            print(f"\nFirst 10 'OUT' lines for {filename}:")
            for num, content in first_10_out:
                print(f"{num}: {content}")

        # Convert the list to a pandas DataFrame
        df = pd.DataFrame(data)
        
        # Save the DataFrame to a CSV file in the output directory
        output_file_path = os.path.join(output_directory, f'{filename}.csv')
        df.to_csv(output_file_path, index=False, encoding='utf-8')
        
        print(f"Data saved to {output_file_path}")

if __name__ == '__main__':
    main()

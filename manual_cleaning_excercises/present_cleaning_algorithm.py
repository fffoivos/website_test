import os
import re

# Define the directory paths
input_directory = '/home/fivos/Projects/GlossAPI/manual_cleaning_excercises/check_papers/1-50'
# Outputs here:
output_directory = os.path.join(input_directory, 'cleaning_algo_presentation1-50_v2')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Intended match: Greek_words, optional space, more than 3 dots, optional space and/or "σελ.", finally a number and nothing else concatenated to it.
#   eg 'ΠΡΟΚΑΤΑΡΚΤΙΚΕΣ ΕΡΓΑΣΙΕΣ ΣΥΝΤΗΡΗΣΗΣ ........................................................50'
index_pattern = re.compile(r"([α-ωΑ-Ωά-ώ\d:]+)\s{0,2}(?:[.ο•]{4,}|(?:[.ο•]+\s{1,2})+[.ο•]+)(\s{0,2}σελ\.)?\s{0,2}\d+(?!\S)")

# Pattern for bibliography
bibliography_pattern = re.compile(r".*βιβλιογραφ[ιί]α.*")

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
    # Remove any non-printable characters and collapse whitespace
    concat_line = re.sub(r'[^\x20-\x7Eα-ωΑ-Ω]', '', line)  # Keeps only printable ASCII and Greek characters
    concat_line = re.sub(r'\s+', '', concat_line)  # Remove remaining spaces
    if len(concat_line) < 40:
        concat_line = concat_line.lower()
        return bibliography_pattern.match(concat_line)
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
        print(f"processing {filename}")
        last_index_line_number, bibliography_line_number, lines = process_file(file_path)
        
        # Prepare output lines
        output_lines = []
        inside_content = False
        for line_number, line in enumerate(lines, 1):
            if line_number == last_index_line_number + 1:
                # Start of content
                output_lines.append("[=== ΑΡΧΉ ΚΑΘΑΡΙΣΜΈΝΟΥ ΑΡΧΕΊΟΥ ===]\n")
                inside_content = True
            if line_number == bibliography_line_number + 1:
                # End of content
                output_lines.append("[=== ΤΈΛΟΣ ΚΑΘΑΡΙΣΜΈΝΟΥ ΑΡΧΕΊΟΥ ===]\n")
                inside_content = False
            if inside_content:
                output_lines.append(line)
            else:
                output_lines.append("[ΕΚΤΟΣ] " + line)
        
        # If content goes till the end of file, ensure we add the end marker
        if inside_content:
            output_lines.append("[=== ΤΈΛΟΣ ΚΑΘΑΡΙΣΜΈΝΟΥ ΑΡΧΕΊΟΥ ===]\n")
        
        # Write the transformed lines to the output file
        output_file_path = os.path.join(output_directory, filename)
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.writelines(output_lines)

if __name__ == '__main__':
    main()

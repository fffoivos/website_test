import os
import re
import unicodedata
import math

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
        match = bibliography_pattern.match( concat_line.lower() )
        return match
    else:
        return False

def main():
    # List to store distances from bibliography_line to end of file
    file_distances = []

    # Process each file in the input directory
    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        
        # Skip directories and non-text files
        if os.path.isdir(file_path) or not filename.endswith('.txt'):
            continue
        
        # Process the file
        print(f"Processing {filename}")
        last_index_line_number, bibliography_line_number, lines = process_file(file_path)
        
        txt_length = len(lines)
        distance = txt_length - bibliography_line_number  # Distance from bibliography_line to end of file
        
        # Store the filename and distance
        file_distances.append((filename, distance))
        
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
    
    # Calculate the top x% files with the longest distances
    total_files = len(file_distances)
    top_n = max(1, math.ceil(total_files * 0.2))
    # Sort the files by distance in descending order
    sorted_files = sorted(file_distances, key=lambda x: x[1], reverse=True)
    top_files = sorted_files[:top_n]
    
    # Print the names and distances of the top 5% files
    print("\nTop 5% files with the longest distance from bibliography_line to end of file:")
    for filename, distance in top_files:
        print(f"{filename}: {distance} lines after bibliography_line")

if __name__ == '__main__':
    main()

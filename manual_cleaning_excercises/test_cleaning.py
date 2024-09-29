import os
import re
import unicodedata


# Define the directory paths
input_directory = '/home/fivos/Projects/GlossAPI/manual_cleaning_excercises/check_papers'
# Outputs here:
output_directory = os.path.join(input_directory, 'extracted_content')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Intended match: Greek_words, optional space, more than 3 dits, optional space and/or "σελ.", finally a number and nothing else concatenated to it.
#   eg 'ΠΡΟΚΑΤΑΡΚΤΙΚΕΣ ΕΡΓΑΣΙΕΣ ΣΥΝΤΗΡΗΣΗΣ ........................................................50'
index_pattern = re.compile(r"([α-ωΑ-Ωά-ώ\d\s:]+\S+)\s*\.{4,}\s*(σελ\.\s*)?\s?(\d+)(?!\S)")

# Pattern for bibliography
bibliography_pattern = re.compile(r"^\s*βιβλιογραφ[ιί]α\s*$", re.IGNORECASE)

def process_file(file_path):
    last_index_line_number = 0
    bibliography_line_number = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        # Set bibliography_line_number to last line number by default
        bibliography_line_number = len(lines)
        
        for line_number, line in enumerate(lines, 1):
            # Check for index entries
            if index_pattern.search(line):
                last_index_line_number = line_number
            
            # Check for bibliography
            if bibliography_pattern.match(line):
                bibliography_line_number = line_number - 1
                break  # Stop processing after finding bibliography
    
    # Extract content from last index to bibliography or end of file
    content_lines = lines[last_index_line_number:bibliography_line_number]
    
    return last_index_line_number, bibliography_line_number, content_lines

# Process all .txt files in the directory
for filename in os.listdir(input_directory):
    if filename.endswith('.txt'):
        input_file_path = os.path.join(input_directory, filename)
        last_index_line, bibliography_line, content = process_file(input_file_path)
        
        print(f"\nFile: {filename}")
        print(f"New first line: {last_index_line}")
        print(f"New last line: {bibliography_line if bibliography_line != len(content) else 'None; defautled to last line'}")
        
        if content:
            output_file_path = os.path.join(output_directory, filename)
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.writelines(content)
            print(f"Extracted content saved to: {output_file_path}")
            print(f"Extracted {len(content)} lines")
        else:
            print("No content extracted.")

print("\nProcessing complete.")

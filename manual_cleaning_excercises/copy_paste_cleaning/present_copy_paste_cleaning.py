import os
import re
import unicodedata
import math

# Define the directory paths
input_directory = '/home/fivos/Desktop/Projects/GlossAPI/raw_txt/sxolika/paste_texts'
# Outputs here:
output_directory = os.path.join(input_directory, 'cleaning_presentation')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Intended match: Greek_words, optional space, more than 3 dots, optional space and/or "σελ.", finally a number and nothing else concatenated to it.
#   eg 'ΠΡΟΚΑΤΑΡΚΤΙΚΕΣ ΕΡΓΑΣΙΕΣ ΣΥΝΤΗΡΗΣΗΣ ........................................................50'
index_pattern = re.compile(r"^([Α-Ω]\. )?((\d{1,2}\.)*(\d)?)? {0,4}(\.*)\s{0,2}[Α-ΩΆ-ΏA-Z](([a-zA-Zα-ωΑ-Ωά-ώ-.:])+ \d{0,2})+\s{0,4}(\.)*(\s{0,2}(σελ\.|Σελ\.\:|))?\s{0,4}\d+$")

# Pattern for bibliography
bibliography_pattern = re.compile(r".*βιβλιογραφια.*")
legal_statement_pattern = re.compile(r".*Βάσει του ν\. 3966/2011 τα διδακτικά βιβλία.*", re.IGNORECASE)
pagination_pattern = re.compile(r"^((\d){1,2}|(. (\d) .)|\[(\d)\]|(vi{0,3}))$")

def find_bibliography_line(line):
    # Removes combined characters (accents) from Greek letters
    accentless_line = ''.join(c for c in unicodedata.normalize('NFD', line) if unicodedata.category(c) != 'Mn')
    # Remove any non-printable characters and collapse whitespace
    concat_line = re.sub(r'[^α-ωΑ-Ω]', '', accentless_line)  # Keeps only Greek characters
    if len(concat_line) < 40:
        match = bibliography_pattern.match(concat_line.lower())
        return match
    else:
        return False

def find_legal_statement_line(line):
    # Check if the line matches the legal statement pattern
    match = legal_statement_pattern.match(line.lower())
    return match

def find_page_number(line):
    match = pagination_pattern.search(line)
    if match:
        page = match.group(1)
        if page.isdigit():
            return int(page)
        else:
            if page == "v": return 5
            elif page == "vi": return 6
            elif page == "vii": return 7
            elif page == "viii": return 8
            else: return 0
    return 0

def process_file(file_path):
    last_index_line_number = 0
    bibliography_line_number = None
    legal_statement_line_number = None
    page_number = 0  # To store the line number of the page seven match
    page_number_line = 1

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        # Set bibliography_line_number to last line number by default
        txt_length = len(lines)
        bibliography_line_number = txt_length
        
        for line_number, line in enumerate(lines, 1):
            # First, check for index entries (within the first half of the text)
            if (line_number / txt_length) < 0.1:
                if index_pattern.search(line):
                    last_index_line_number = line_number
                
                # Simultaneously check for the seventh page patterns and store the line if found
                if page_number not in {7, 8}:
                    new_page_number = find_page_number(line)
                    if new_page_number - page_number > 0:
                        page_number = new_page_number
                        page_number_line = line_number
            
            # Check for bibliography after 90% of the document
            if (line_number / txt_length) > 0.9 and find_bibliography_line(line):
                bibliography_line_number = line_number - 1
                break  # Stop processing after finding bibliography
            
            # If bibliography not found, check for legal statement
            if bibliography_line_number == txt_length and find_legal_statement_line(line):
                bibliography_line_number = line_number - 1
        
        # If no index pattern was found, fall back to the seventh page line number if it exists
        if last_index_line_number == 0 and page_number_line is not None:
            last_index_line_number = page_number_line
    
    return last_index_line_number, bibliography_line_number, lines

def print_presentation(file_distances):
    # Calculate the top x% files with the longest distances
    total_files = len(file_distances)
    prcnt = 0.2
    top_n = max(1, math.ceil(total_files * prcnt))
    # Sort the files by distance in descending order
    sorted_files = sorted(file_distances, key=lambda x: x[1], reverse=True)
    top_files = sorted_files[:top_n]
    
    # Print the names and distances of the top 5% files
    print(f"\nTop {str(prcnt*100)}% files with the longest distance from bibliography_line to end of file:")
    for filename, distance in top_files:
        print(f"{filename}: {distance} lines after bibliography_line")

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
        
        #print_presentation(file_distances)
    

if __name__ == '__main__':
    main()

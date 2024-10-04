import os
import re
import unicodedata

# Define the directory paths
input_directory = '/home/fivos/Desktop/New Folder/Sxolika/filtered_by_JSON/cleaned_filtered_extracted_txt/'
# Outputs here:
output_directory = os.path.join(input_directory, 'fine_cleaning_v2')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Patterns to find "βιβλιογραφια" and "κεφαλαιο"
bibliography_pattern = re.compile(r".*βιβλιογραφια.*", re.IGNORECASE)
bibliography_end_ofline = re.compile(r".*\d+(?:\.\d+)?\s+Αναφορές\s*[-–]\s*Βιβλιογραφία($|\n)", re.IGNORECASE | re.UNICODE)

kefalaio_pattern = re.compile(r".*κεφαλαιο\s.*", re.IGNORECASE)
# ενότητα
enotita_pattern = re.compile(r".*ενότητα\s.*", re.IGNORECASE)
# κεφ.
kef_pattern = re.compile(r".*κεφ\.\s.*", re.IGNORECASE)
#eg 3.  Βασικά στοιχεία γλώσσας προγραμματισμού or 1.2
chapter_heading_pattern = re.compile(r"(?!.)\s{0,2}\f?(\d{1,2}\.)\d{0,2}\s+(.{0,50})", re.UNICODE | re.IGNORECASE)

def find_bibliography_line(line):
    match = False
    # Removes combined characters (accents) from Greek letters
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    # Remove any non-Greek characters
    concat_line = re.sub(r'[^α-ωΑ-Ω]', '', accentless_line)  # Keeps only Greek letters
    if len(concat_line) < 40:
        match = bibliography_pattern.search(concat_line.lower())
    if not match:
        match = bibliography_end_ofline.search(line.lower())
    return match

def find_chapter_line(line):
    match = False
    # Removes combined characters (accents) from Greek letters
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    # Remove any non-Greek characters
    concat_line = re.sub(r'[^α-ωΑ-Ω]', '', accentless_line)  # Keeps only Greek letters
    if len(concat_line) < 20:
        match = kefalaio_pattern.search(accentless_line.lower())
        if not match:
            match = enotita_pattern.search(accentless_line.lower())
        if not match:
            match = kef_pattern.search(accentless_line.lower())
    elif chapter_heading_pattern.search(line):
        return True
    return match

def process_file(file_path):
    ranges_to_replace = []
    in_bibliography_section = False
    start_line_number = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        txt_length = len(lines)

        for line_number, line in enumerate(lines, 1):
            if line_number/txt_length >0.1 and find_bibliography_line(line):
                if not in_bibliography_section:
                    in_bibliography_section = True
                    start_line_number = line_number + 1  # Start after "βιβλιογραφια" line
            elif in_bibliography_section and find_chapter_line(line):
                # End of the range
                end_line_number = line_number - 1  # End before "κεφαλαιο" line
                if start_line_number <= end_line_number:
                    ranges_to_replace.append((start_line_number, end_line_number))
                in_bibliography_section = False
                start_line_number = None

        # If we reach the end and still in bibliography section
        if in_bibliography_section and start_line_number is not None:
            # Range goes till end of file
            end_line_number = txt_length
            if start_line_number <= end_line_number:
                ranges_to_replace.append((start_line_number, end_line_number))

    return ranges_to_replace, lines

def is_line_in_ranges(line_number, ranges):
    for start, end in ranges:
        if start <= line_number <= end:
            return True
    return False

def main():
    # Process each file in the input directory
    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        
        # Skip directories and non-text files
        if os.path.isdir(file_path) or not filename.endswith('.txt'):
            continue
        
        # Process the file
        ranges_to_replace, lines = process_file(file_path)
        if(ranges_to_replace):
            print(filename, " εχει εσωτερικη βιβλιογραφια")
        
        # Prepare output lines
        output_lines = []
        for line_number, line in enumerate(lines, 1):
            if is_line_in_ranges(line_number, ranges_to_replace):
                output_lines.append("[ΕΚΤΟΣ]"+line)
            else:
                output_lines.append(line)
        
        # Write the transformed lines to the output file
        output_file_path = os.path.join(output_directory, filename)
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.writelines(output_lines)

if __name__ == '__main__':
    main()

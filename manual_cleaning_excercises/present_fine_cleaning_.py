import os
import re
import csv
import unicodedata

# Define the directory paths
input_directory = '/home/fivos/Desktop/New Folder/Sxolika/filtered_by_JSON/cleaned_filtered_extracted_txt/'
# Outputs here:
output_directory = os.path.join(input_directory, 'fine_cleaning_v2')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Patterns to find "(οτιδηποτε εδω) βιβλιογραφια, ελληνικα ή αγγλικα και τελος"
bibliography_pattern = re.compile(r".*βιβλιογραφια([-–α-ωΑ-Ω\w]{0,10})($|\n)", re.UNICODE)
bibliography_atend = re.compile(r"βιβλιογραφια {0,5}($|\n)", re.UNICODE)
#bibliography_atend = re.compile(r".*Βιβλιογραφια($|\n)", re.IGNORECASE)

#bibliography_end_ofline = re.compile(r".*\d+(?:\.\d+)? +Αναφορές *[-–]? *Βιβλιογραφία($|\n)", re.UNICODE)

kefalaio_pattern = re.compile(r".*(κεφαλαιο:? {0,4}.*)(\n|$)", re.UNICODE) # .{0,3}(κεφαλαιο\s.*)(\n|$) ίσως να είναι καλύτερο αυτό
kefalaio_atend_pattern = re.compile(r"(\f| )(κεφαλαιο:? {0,4}.*)(\n|$)", re.UNICODE) # .{0,3}(κεφαλαιο\s.*)(\n|$) ίσως να είναι καλύτερο αυτό

# ενότητα
enotita_pattern = re.compile(r".*(ενοτητα .*\d+.*)$", re.UNICODE)
# κεφ.
kef_pattern = re.compile(r".*κεφ\.\s.*", re.UNICODE)
#eg 3.  Βασικά στοιχεία γλώσσας προγραμματισμού or 1.2
#chapter_heading_pattern = re.compile(r"[^\d]{0,50}?(\d\d?)\.[^\d]+") πολύ γενικό
section_number = re.compile(r"(\d\d?)\.(\d\d?)\.(\d\d?)")


def remove_accents(line):
    line = line.lower()
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    return accentless_line


def find_bibliography_line(line):
    match = False
    # Removes combined characters (accents) from Greek letters
    accentless_line = remove_accents(line)
    # Remove any non-Greek characters
    concat_line = re.sub(r'\s', '', accentless_line)
    if len(concat_line) < 40:
        match = bibliography_pattern.search(concat_line)
    if not match:
        match = bibliography_atend.search(concat_line)
    return match


def find_chapter_line(line):
    match = False
    # Removes combined characters (accents) from Greek letters
    accentless_line = remove_accents(line)
    # Remove any non-Greek characters
    concat_line = re.sub(r'\s', '', accentless_line)
    if len(concat_line) < 40:
        match = kefalaio_pattern.search(accentless_line)
    if len(concat_line) < 30:
        if not match:
            match = enotita_pattern.search(accentless_line)
        if not match:
            match = kef_pattern.search(accentless_line)
        if not match:
            match = section_number.search(accentless_line)
    if not match:
        match = kefalaio_atend_pattern.search(accentless_line)
    return match

      
def process_file(file_path):
    ranges_to_replace = []
    in_bibliography_section = False
    start_line_number = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        txt_length = len(lines)

        for line_number, line in enumerate(lines, 1):
            # Check if we have reached the bibliography section
            if not in_bibliography_section and line_number / txt_length > 0.02 and find_bibliography_line(line):
                in_bibliography_section = True
                start_line_number = line_number + 1  # Start after "βιβλιογραφια" line

            # If we are in the bibliography section and find a new chapter, close the range
            elif in_bibliography_section and find_chapter_line(line):
                end_line_number = line_number - 1  # End before the "chapter" line
                if start_line_number <= end_line_number:
                    ranges_to_replace.append((start_line_number, end_line_number))
                in_bibliography_section = False  # Reset for the next potential bibliography section
                start_line_number = None

        # If we reach the end of the file and still in bibliography section, close the range
        if in_bibliography_section and start_line_number is not None:
            end_line_number = txt_length  # End at the last line
            if start_line_number <= end_line_number:
                ranges_to_replace.append((start_line_number, end_line_number))

    return ranges_to_replace, lines

def is_line_in_ranges(line_number, ranges):
    for start, end in ranges:
        if start <= line_number <= end:
            return True
    return False


def main():
    # Prepare CSV output file
    csv_output_path = os.path.join(output_directory, 'filtering_presentation.csv')
    
    # Open the CSV file for writing
    with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Write the header row in the CSV
        csvwriter.writerow(['Filename', 'Total [ΕΚΤΟΣ] Lines', 'Percentage [ΕΚΤΟΣ]', 'Internal Bibliography'])

        # Process each file in the input directory
        for filename in os.listdir(input_directory):
            file_path = os.path.join(input_directory, filename)
            
            # Skip directories and non-text files
            if os.path.isdir(file_path) or not filename.endswith('.txt'):
                continue
            
            # Process the file
            ranges_to_replace, lines = process_file(file_path)
            if ranges_to_replace:
                print(filename, " εχει εσωτερικη βιβλιογραφια")
            
            # Prepare output lines and count [ΕΚΤΟΣ] lines
            output_lines = []
            total_ektos_lines = 0
            for line_number, line in enumerate(lines, 1):
                if is_line_in_ranges(line_number, ranges_to_replace):
                    output_lines.append("[ΕΚΤΟΣ]" + line)
                    total_ektos_lines += 1
                else:
                    output_lines.append(line)
            
            # Calculate percentage of [ΕΚΤΟΣ] lines
            total_lines = len(lines)
            ektos_percentage = (total_ektos_lines / total_lines) * 100 if total_lines > 0 else 0
            
            # Determine the value of internal_bib (1 if ranges_to_replace has elements, 0 otherwise)
            internal_bib = 1 if ranges_to_replace else 0

            # Write data to CSV: filename, total [ΕΚΤΟΣ] lines, percentage, and internal_bib
            csvwriter.writerow([filename, total_ektos_lines, f'{ektos_percentage:.2f}%', internal_bib])
            
            # Write the transformed lines to the output file
            output_file_path = os.path.join(output_directory, filename)
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.writelines(output_lines)


if __name__ == '__main__':
    main()

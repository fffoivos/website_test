import os
import re
import csv
import unicodedata

# Define the directory paths
input_directory = '/home/fivos/Desktop/paste_text_Filtered/xondrikos_katharismos_papers/'
# Outputs here:
output_directory = os.path.join(input_directory, 'fine_cleaning_v3')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Patterns to find bibliography lines
bibliography_pattern = re.compile(r".*βιβλιογραφια([-–α-ωΑ-Ω\w]{0,10})($|\n)", re.UNICODE)
bibliography_atend = re.compile(r"βιβλιογραφια {0,5}($|\n)", re.UNICODE)

# Corrected pattern to find lines with four or more dots
dotted_pattern = re.compile(r"\.{5,}")

# Patterns to find chapter lines
kefalaio_pattern = re.compile(r".*(κεφαλαιο:? {0,4}.*)(\n|$)", re.UNICODE)
kefalaio_atend_pattern = re.compile(r"(\f| )(κεφαλαιο:? {0,4}.*)(\n|$)", re.UNICODE)
enotita_pattern = re.compile(r".*(ενοτητα .*\d+.*)$", re.UNICODE)
kef_pattern = re.compile(r".*κεφ\.\s.*", re.UNICODE)
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
    accentless_line = remove_accents(line)
    concat_line = re.sub(r'\s', '', accentless_line)
    if len(concat_line) < 40:
        match = bibliography_pattern.search(concat_line)
    if not match:
        match = bibliography_atend.search(concat_line)
    return match


def find_chapter_line(line):
    match = False
    accentless_line = remove_accents(line)
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


def find_index_line(line):
    return bool(dotted_pattern.search(line))


def process_file(lines):
    ranges_to_replace = []
    in_bibliography_section = False
    start_line_number = None

    txt_length = len(lines)
    lines_to_exclude = set()

    for line_number, line in enumerate(lines, 1):
        # Check for dotted lines
        if find_index_line(line):
            lines_to_exclude.add(line_number)

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

    return ranges_to_replace, lines_to_exclude


def main():
    # Prepare CSV output file
    csv_output_path = os.path.join(output_directory, 'filtering_presentation.csv')
    
    # Open the CSV file for writing
    with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Write the header row in the CSV
        csvwriter.writerow([
            'Filename',
            'Total Excluded Lines',
            'Excluded Percentage',
            'Total Bibliography Lines',
            'Bibliography Percentage',
            'Total Dotted Lines',
            'Dotted Percentage',
            'Internal Bibliography',
            'Contains Dotted Lines'
        ])

        # Process each file in the input directory
        for filename in os.listdir(input_directory):
            file_path = os.path.join(input_directory, filename)
            
            # Skip directories and non-text files
            if os.path.isdir(file_path) or not filename.endswith('.txt'):
                continue
            
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Process the file
            ranges_to_replace, lines_to_exclude = process_file(lines)
            if ranges_to_replace:
                print(filename, " έχει εσωτερική βιβλιογραφία")

            # Get sets of line numbers
            bibliography_lines_set = set()
            for start_line, end_line in ranges_to_replace:
                bibliography_lines_set.update(range(start_line, end_line + 1))

            dotted_lines_set = lines_to_exclude

            excluded_lines_set = bibliography_lines_set.union(dotted_lines_set)

            # Prepare output lines
            output_lines = []
            for line_number, line in enumerate(lines, 1):
                if line_number in excluded_lines_set:
                    output_lines.append("[ΕΚΤΟΣ]" + line)
                else:
                    output_lines.append(line)
            
            # Calculate counts and percentages
            total_lines = len(lines)
            total_bibliography_lines = len(bibliography_lines_set)
            total_dotted_lines = len(dotted_lines_set)
            total_excluded_lines = len(excluded_lines_set)

            bibliography_percentage = (total_bibliography_lines / total_lines) * 100 if total_lines > 0 else 0
            dotted_percentage = (total_dotted_lines / total_lines) * 100 if total_lines > 0 else 0
            excluded_percentage = (total_excluded_lines / total_lines) * 100 if total_lines > 0 else 0

            internal_bib = 1 if total_bibliography_lines > 0 else 0
            contains_dotted_lines = 1 if total_dotted_lines > 0 else 0

            # Write data to CSV
            csvwriter.writerow([
                filename,
                total_excluded_lines,
                f'{excluded_percentage:.2f}%',
                total_bibliography_lines,
                f'{bibliography_percentage:.2f}%',
                total_dotted_lines,
                f'{dotted_percentage:.2f}%',
                internal_bib,
                contains_dotted_lines
            ])
            
            # Write the transformed lines to the output file
            output_file_path = os.path.join(output_directory, filename)
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.writelines(output_lines)


if __name__ == '__main__':
    main()

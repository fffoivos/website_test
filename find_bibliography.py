import os
import re

# Path to the directory
directory_path = '/home/fivos/Projects/GlossAPI/manual_cleaning_excercises/check_papers'

# Regular expression to detect "βιβλιογραφία" or "βιβλιογραφια" (with any capitalization) on its own
bibliography_pattern = re.compile(r"^\s*βιβλιογραφ[ιί]α\s*$", re.IGNORECASE)

# Function to check if "bibliography" exists on its own on a single line
def check_bibliography_on_single_line(file_path):
    lines_with_bibliography = []

    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Check each line for "βιβλιογραφια" or "βιβλιογραφία" on its own
    for idx, line in enumerate(lines):
        if re.match(bibliography_pattern, line):
            lines_with_bibliography.append((idx + 1, line.strip()))

    return lines_with_bibliography

# Iterate over all .txt files in the directory
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(directory_path, filename)
        print(f"Processing file: {filename}")

        # Check each file for the bibliography pattern on a single line
        lines_with_bibliography = check_bibliography_on_single_line(file_path)
        
        if lines_with_bibliography:
            print(f"\n'βιβλιογραφια' or 'βιβλιογραφία' found on its own in the following lines of {filename}:")
            for line_number, content in lines_with_bibliography:
                print(f"Line {line_number}: {content}")
        else:
            print(f"No standalone 'βιβλιογραφια' or 'βιβλιογραφία' found in {filename}.")

        print("="*50)

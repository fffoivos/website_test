import os
import re

# Set your directory paths
input_directory = "/home/fivos/Desktop/cleaning_algo_presentation1-50_v3/"
inpages_directory = "/home/fivos/Desktop/test_2nd_bibliography_pages/INPAGES/"
outpages_directory = "/home/fivos/Desktop/test_2nd_bibliography_pages/OUTPAGES"

# Ensure output directories exist
os.makedirs(inpages_directory, exist_ok=True)
os.makedirs(outpages_directory, exist_ok=True)

# Regex pattern for matching the page markers
page_marker_regex = re.compile(r'.+\.(indd|indb)\s{0,3}\d+')

# Function to find all page ranges based on the regex match
def split_into_pages_by_regex(content):
    lines = content.splitlines()
    page_indices = []

    # Find all the lines where the regex matches (page markers)
    for i, line in enumerate(lines):
        if page_marker_regex.match(line):
            page_indices.append(i)

    # Split the content into pages using the found indices
    pages = []
    for i in range(len(page_indices)):
        start = page_indices[i]
        end = page_indices[i + 1] if i + 1 < len(page_indices) else len(lines)
        page_content = '\n'.join(lines[start:end]).strip()
        pages.append(page_content)

    return pages

# Function to split text in half and take the second half
def split_in_half(text):
    middle_index = len(text) // 2
    return text[middle_index:]

# Function to check if a page contains a line that starts with "[ΕΚΤΟΣ]"
def contains_ekto(page):
    lines = page.splitlines()
    for line in lines:
        if line.startswith("[ΕΚΤΟΣ]"):
            return True
    return False

# Function to clean the content by:
# 1. Removing "[=== ΤΈΛΟΣ ΚΑΘΑΡΙΣΜΈΝΟΥ ΑΡΧΕΊΟΥ ===]"
# 2. Removing "[ΕΚΤΟΣ]" but keeping the rest of the line
# 3. Converting the content to lowercase
def clean_content(content):
    cleaned_lines = []
    for line in content.splitlines():
        # Remove the "ΤΈΛΟΣ ΚΑΘΑΡΙΣΜΈΝΟΥ ΑΡΧΕΊΟΥ" line entirely
        if "[=== ΤΈΛΟΣ ΚΑΘΑΡΙΣΜΈΝΟΥ ΑΡΧΕΊΟΥ ===]" in line:
            continue
        # Remove "[ΕΚΤΟΣ]" but keep the rest of the line
        line = re.sub(r'\[ΕΚΤΟΣ\]', '', line)
        # Convert the line to lowercase
        cleaned_lines.append(line.lower())
    return '\n'.join(cleaned_lines)

# Process each text file
for filename in os.listdir(input_directory):
    if filename.endswith(".txt"):
        file_path = os.path.join(input_directory, filename)
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Take the second half of the file
        second_half = split_in_half(content)
        
        # Split the content into pages based on the page marker regex
        pages = split_into_pages_by_regex(second_half)
        
        # Get the second page that doesn't contain a line starting with "[ΕΚΤΟΣ]"
        second_page = None
        if len(pages) > 1 and not contains_ekto(pages[1]):
            second_page = pages[1]
        
        # Get the first page that contains a line starting with "[ΕΚΤΟΣ]"
        ekto_page = None
        for i,page in enumerate(pages):
            if contains_ekto(page):
                ekto_page = pages[i+1]
                break
        
        # Clean and save the second page in the INPAGES folder
        if second_page:
            cleaned_second_page = clean_content(second_page)
            inpage_filename = os.path.join(inpages_directory, f"{os.path.splitext(filename)[0]}_INPAGE.txt")
            with open(inpage_filename, 'w', encoding='utf-8') as inpage_file:
                inpage_file.write(cleaned_second_page)
        
        # Clean and save the first "[ΕΚΤΟΣ]" page in the OUTPAGES folder
        if ekto_page:
            cleaned_ekto_page = clean_content(ekto_page)
            outpage_filename = os.path.join(outpages_directory, f"{os.path.splitext(filename)[0]}_OUTPAGE.txt")
            with open(outpage_filename, 'w', encoding='utf-8') as outpage_file:
                outpage_file.write(cleaned_ekto_page)

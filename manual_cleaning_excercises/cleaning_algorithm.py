import os
import re
import unicodedata

# Define the directory paths
input_directory = '/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs'
output_directory = os.path.join(input_directory, 'cleaned_filtered_extracted_txt')

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Regex patterns
index_pattern = re.compile(r"([α-ωΑ-Ωά-ώ\d:]+)\s{0,4}(?:[.ο•]{4,}|(?:[.ο•]+\s{1,2})+[.ο•]+)(\s{0,2}σελ\.)?\s{0,4}\d+(?!\S)")
bibliography_pattern = re.compile(r".*βιβλιογραφια.*", re.IGNORECASE)
legal_statement_pattern = re.compile(r".*Βάσει του ν\. 3966/2011 τα διδακτικά βιβλία.*", re.IGNORECASE)
page_seven_adobe_format = re.compile(r".+\.(indd|indb)\s{0,3}[7]")
page_seven_other_format = re.compile(r"\d{1,2}\/\d{1,2}\/\d{2}\s+\d{1,2}:\d{2}\s+(?:AM|PM)\s+Page\s+7")

# Functions
def find_bibliography_line(line):
    accentless_line = ''.join(c for c in unicodedata.normalize('NFD', line) if unicodedata.category(c) != 'Mn')
    concat_line = re.sub(r'[^α-ωΑ-Ω]', '', accentless_line)
    return bibliography_pattern.match(concat_line.lower()) if len(concat_line) < 40 else False

def find_legal_statement_line(line):
    return legal_statement_pattern.match(line.lower())

def process_file(file_path):
    last_index_line_number = 0
    bibliography_line_number = None
    legal_statement_line_number = None
    seventh_page_line_number = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        txt_length = len(lines)
        bibliography_line_number = txt_length
        
        for line_number, line in enumerate(lines, 1):
            if (line_number / txt_length) < 0.5 and index_pattern.search(line):
                last_index_line_number = line_number
            
            if (line_number / txt_length) > 0.9 and find_bibliography_line(line):
                bibliography_line_number = line_number - 1
                break
            
            if bibliography_line_number == txt_length and find_legal_statement_line(line):
                bibliography_line_number = line_number - 1
        
        if last_index_line_number == 0 and seventh_page_line_number:
            last_index_line_number = seventh_page_line_number

    return last_index_line_number, bibliography_line_number, lines

def main():
    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        
        if os.path.isdir(file_path) or not filename.endswith('.txt'):
            continue
        
        print(f"Processing {filename}")
        last_index_line_number, bibliography_line_number, lines = process_file(file_path)
        
        txt_length = len(lines)
        distance = txt_length - bibliography_line_number
        
        output_lines = []
        inside_content = False
        for line_number, line in enumerate(lines, 1):
            if line_number == last_index_line_number + 1:
                inside_content = True
            if line_number == bibliography_line_number + 1:
                inside_content = False
            if inside_content:
                output_lines.append(line)
        
        output_file_path = os.path.join(output_directory, filename)
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.writelines(output_lines)

if __name__ == '__main__':
    main()

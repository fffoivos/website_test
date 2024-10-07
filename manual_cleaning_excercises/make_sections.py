import os
import csv
import re
from typing import List, Tuple

def is_capitalized_line(line: str) -> bool:
    return bool(re.match(r'^[Α-ΩΆΈΉΊΌΎΏ\s:-]+$', line.strip()))

def extract_page_heading(text: str) -> Tuple[str, str]:
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if is_capitalized_line(line):
            return line.strip(), '\n'.join(lines[i+1:])
    return '', text

def process_text(text: str) -> Tuple[str, str, str, str]:
    page_heading, text = extract_page_heading(text)
    lines = text.split('\n')
    section_heading = ''
    cleaned_text = []
    removed_uppercase = []
    
    i = 0
    while i < len(lines):
        if is_capitalized_line(lines[i]):
            if i + 1 < len(lines) and not is_capitalized_line(lines[i+1]):
                section_heading = lines[i].strip()
                i += 1
            else:
                start = i
                while i < len(lines) and is_capitalized_line(lines[i]):
                    i += 1
                removed_uppercase.extend(lines[start:i])
        else:
            cleaned_text.append(lines[i])
        i += 1
    
    return page_heading, section_heading, '\n'.join(cleaned_text), '\n'.join(removed_uppercase)

def process_csv_file(input_file: str, output_folder: str):
    print(f"Processing file: {os.path.basename(input_file)}")
    output_rows = []
    index = 1

    with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        current_section = ''
        current_text = ''
        current_pages = []
        current_page_headings = []

        for row in reader:
            page_heading, section_heading, cleaned_text, removed_uppercase = process_text(row['text'])
            
            if section_heading:
                if current_section:
                    output_rows.append({
                        'index': index,
                        'text': current_text.strip().replace('\n', ' '),
                        'pages': '-'.join(map(str, current_pages)),
                        'page_headings': ', '.join(current_page_headings),
                        'section_heading': current_section,
                        'removed_uppercase': ''
                    })
                    index += 1
                current_section = section_heading
                current_text = cleaned_text
                current_pages = [int(row['page'])]
                current_page_headings = [page_heading]
            else:
                current_text += ' ' + cleaned_text
                current_pages.append(int(row['page']))
                current_page_headings.append(page_heading)
            
            if removed_uppercase:
                output_rows.append({
                    'index': index,
                    'text': '',
                    'pages': row['page'],
                    'page_headings': page_heading,
                    'section_heading': '',
                    'removed_uppercase': removed_uppercase.replace('\n', ' ')
                })
                index += 1

        # Add the last section
        if current_section:
            output_rows.append({
                'index': index,
                'text': current_text.strip().replace('\n', ' '),
                'pages': '-'.join(map(str, current_pages)),
                'page_headings': ', '.join(current_page_headings),
                'section_heading': current_section,
                'removed_uppercase': ''
            })

    # Write to output TSV
    output_file = os.path.join(output_folder, os.path.basename(input_file).replace('.csv', '_split.tsv'))
    with open(output_file, 'w', newline='', encoding='utf-8') as tsvfile:
        fieldnames = ['index', 'text', 'pages', 'page_headings', 'section_heading', 'removed_uppercase']
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(output_rows)

def process_csv_files(input_folder: str):
    output_folder = os.path.join(input_folder, "section_split")
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith('.csv'):
            input_file = os.path.join(input_folder, filename)
            process_csv_file(input_file, output_folder)

# Usage
input_folder = '/home/fivos/Desktop/cleaned_filtered_extracted_txt/fine_cleaning/extracted_pages'
process_csv_files(input_folder)
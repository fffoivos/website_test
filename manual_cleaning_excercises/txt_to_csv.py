import os
import pandas as pd
import re
from collections import Counter
import unicodedata
import csv

def remove_accents(line):
    line = line.lower()
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line) if unicodedata.category(c) != 'Mn'
    )
    return accentless_line

# Define regex patterns
patterns = [
    r"^(?P<enothta_letter>(ενοτητα|enothta) [α-ωa-z])$",
    r"^(?P<thematikh_enothta>(θεματικη ενοτητα|thematikh enothta) \d+)$",
    r"^(?P<kefalaio_letter>(κεφαλαιο|kefalaio) [α-ωa-z])$",
    r"^(?P<kefalaio_number>(κεφαλαιο|kefalaio) \d+[οo])$",
    r"^(?P<numbered_section>(#\s*)?\d+\.\d+\.\s+([α-ωa-zΑ-ΩA-Z][α-ωa-zάέήίόύώϊϋΐΰ\s]+))$",
    r"^(?P<enothta_number>(ενοτητα|enothta) \d+[ηn])$"
]

# Compile regex patterns
compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

def match_section(text):
    normalized_text = remove_accents(text)
    for pattern in compiled_patterns:
        match = pattern.match(normalized_text)
        if match:
            return text  # Return the original text if there's a match
    return None  # Return None if no match is found

def is_uppercase_greek(text):
    # Pattern to match Greek or Latin uppercase letters, digits, and Greek accent, -, : and a single '.'
    greek_uppercase_pattern = r'^[Α-ΩΆ-ΏA-Z\d:´\- ]+\.?[Α-ΩΆ-ΏA-Z\d:´\- ]+$'
    # Pattern to ensure at least one Greek letter is present
    greek_letter = r'[Α-ΩΆ-Ώ]'
    # Pattern to remove digits at the start or end of the text
    appended_digit = r'^\d{1,3}(\S+)|(\S+)\d{1,3}$'
    digit_at_end_or_start = r'^\d{1,3}|\d{1,3}$'
    cleaned_text = text
    # Check if the entire text matches the pattern and contains at least one Greek letter
    if re.match(greek_uppercase_pattern, text) and re.search(greek_letter, text):
        # Remove digits at the start or end of each word
        if re.match(appended_digit, text):
            cleaned_text = re.sub(digit_at_end_or_start, '', text)
        # Remove any empty strings that might result from the digit removal
        return cleaned_text
    return ''


def process_txt_files(input_folder):
    output_folder = os.path.join(input_folder, 'book_as_csv')
    os.makedirs(output_folder, exist_ok=True)
    
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.csv")
            
            with open(input_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            data = []
            for index, line in enumerate(lines, start=1):
                text = line.strip()
                uppercase_greek = is_uppercase_greek(text)
                up = 1 if uppercase_greek else 0
                
                chapter = match_section(text)
                if chapter is None and uppercase_greek:
                    chapter = uppercase_greek
                else:
                    chapter = chapter or ''
                
                data.append({'index': index, 'text': text, 'UP': up, 'chapter': chapter})
            
            df = pd.DataFrame(data)
            
            # Count repetitions of non-empty chapter entries
            chapter_counts = Counter(df['chapter'][df['chapter'] != ''])
            
            # Remove entries in the 'chapter' column that have more than 1 repeat
            df['chapter'] = df['chapter'].apply(lambda x: '' if x != '' and chapter_counts[x] > 5 else x)
            
            # Remove the repeat_count column as it's no longer needed
            
            # Save the DataFrame as a CSV file with specific settings
            df.to_csv(output_path, index=False, sep='\t', encoding='utf-8-sig', quoting=csv.QUOTE_MINIMAL)
            print(f"Processed {filename} and saved as {os.path.basename(output_path)}")

# Example usage
input_folder = '/home/fivos/Desktop/Projects/GlossAPI/raw_txt/sxolika/paste_texts'
process_txt_files(input_folder)
import os
import re
import pandas as pd

def process_books(input_folder):
    # Create 'cleaned_books' folder if it doesn't exist
    cleaned_folder = os.path.join(input_folder, 'cleaned_books_v1')
    if not os.path.exists(cleaned_folder):
        os.makedirs(cleaned_folder)
    
    # Process each txt file in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_folder, filename)
            print(f"Processing {filename}")
            process_file(file_path, cleaned_folder)

def how_much_l(lines):
    #returns percentage of latin in text
    text = ''.join(lines)
    total_chars = len(text)
    latin_chars = len(re.findall(r'[A-Za-z]', text))
    if total_chars > 0:
        return (latin_chars / total_chars) * 100
    else:
        return 0


def process_file(file_path, cleaned_folder):
    # Read the file lines
    with open(file_path, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()
    
    # Compute the Latin percentage based on the original text
    latin_percentage = how_much_latin(original_lines)

    # Now process the initial exclusions
    # Find the first fully uppercase word in the text
    first_uppercase_line_idx = None
    for idx, line in enumerate(original_lines):
        # Split the line into words
        words = line.strip().split()
        for word in words:
            if word.isupper() and len(word) > 1:
                first_uppercase_line_idx = idx
                break  # Exit the word loop
        if first_uppercase_line_idx is not None:
            break  # Exit the line loop
    
    if first_uppercase_line_idx is None:
        first_uppercase_line_idx = 0  # If no uppercase word found, start from beginning
    
    # Find any line that matches the regex in the last 200 lines
    end_line_idx = len(original_lines)
    search_range = original_lines[-200:] if len(original_lines) >= 200 else original_lines
    end_line_relative_idx = None  # Relative index within search_range
    regex_patterns = [r'^ΤΕΛΟΣ$', r'^Α ?Υ ?Λ ?Α ?Ι ?Α$', r'^ΠΕΡΙΕΧΟΜΕΝΑ$']
    pattern_compiled = [re.compile(pattern) for pattern in regex_patterns]
    
    for idx, line in enumerate(search_range):
        line_stripped = line.strip()
        for pattern in pattern_compiled:
            if pattern.match(line_stripped):
                end_line_relative_idx = idx
                break
        if end_line_relative_idx is not None:
            break
    
    if end_line_relative_idx is not None:
        end_line_idx = len(original_lines) - len(search_range) + end_line_relative_idx
    
    # Now process the lines with initial exclusions
    processed_lines = []
    for idx, line in enumerate(original_lines):
        if idx <= first_uppercase_line_idx:
            # Lines to be excluded at the beginning
            processed_lines.append('[ΕΚΤΟΣ]' + line)
        elif idx >= end_line_idx:
            # Lines to be excluded at the end
            processed_lines.append('[ΕΚΤΟΣ]' + line)
        else:
            processed_lines.append(line)
    
    # Now check if the text has more than 5% Latin characters
    if latin_percentage > 5:
        # Make a DataFrame with every line as a row
        df = pd.DataFrame({'index': range(len(original_lines)), 'line_text': original_lines})
        df['has_latin'] = df['line_text'].apply(has_latin_word)
        
        # Find ranges where has_latin == 0 for 10 or more lines in a row
        ranges_to_keep = find_greek_ranges(df)
        
        # Now rebuild the processed_lines based on the ranges
        new_processed_lines = []
        idx = 0
        while idx < len(df):
            in_greek_range = False
            for start, end in ranges_to_keep:
                if start <= idx <= end:
                    in_greek_range = True
                    break
            if in_greek_range:
                # Keep the line, but apply initial exclusions if any
                if idx <= first_uppercase_line_idx or idx >= end_line_idx:
                    new_processed_lines.append('[ΕΚΤΟΣ]' + df.loc[idx, 'line_text'])
                else:
                    new_processed_lines.append(df.loc[idx, 'line_text'])
            else:
                # Exclude the line
                new_processed_lines.append('[ΕΚΤΟΣ]' + df.loc[idx, 'line_text'])
            idx += 1
        processed_lines = new_processed_lines
    
    # Write the processed_lines to a new file in cleaned_books
    filename = os.path.basename(file_path)
    cleaned_file_path = os.path.join(cleaned_folder, filename)
    with open(cleaned_file_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)

def has_latin_word(text):
    # Function to check if the line has any Latin words longer than two characters
    words = re.findall(r'\b[A-Za-z]{3,}\b', text)
    return 1 if words else 0

def find_greek_ranges(df):
    # Find ranges where has_latin == 0 for 10 or more lines in a row
    greek_ranges = []
    current_start = None
    count = 0
    in_greek_segment = False
    idx = 0
    while idx < len(df):
        if df.loc[idx, 'has_latin'] == 0:
            # Start of potential Greek segment
            start_idx = idx
            count = 1
            idx +=1
            while idx < len(df) and df.loc[idx, 'has_latin'] == 0:
                count +=1
                idx +=1
            if count >=10:
                # Valid Greek segment
                greek_ranges.append((start_idx, idx -1))
            else:
                idx +=1
        else:
            idx +=1

    # Now, find the first segment of 10 lines where has_latin ==1 for 10 in a row
    latin_streak = 0
    latin_streak_start = None
    for idx in range(len(df)):
        if df.loc[idx, 'has_latin'] == 1:
            if latin_streak == 0:
                latin_streak_start = idx
            latin_streak +=1
            if latin_streak >=10:
                # Found a Latin segment of 10 lines
                # Remove any Greek ranges after this point
                new_ranges = []
                for start, end in greek_ranges:
                    if end < latin_streak_start:
                        new_ranges.append((start, end))
                greek_ranges = new_ranges
                break
        else:
            latin_streak = 0
            latin_streak_start = None

    return greek_ranges

if __name__ == "__main__":
    input_folder = "/home/fivos/Desktop/gutenberg"
    process_books(input_folder)

import os
import re
import csv
from collections import Counter
import glob
from typing import Dict, Tuple

def is_greek_char(char):
    """
    Check if a character is Ancient Greek.
    Includes comprehensive Unicode ranges for Ancient Greek.
    """
    basic_ranges = (
        '\u0370' <= char <= '\u03FF' or      # Basic Greek and Coptic
        '\u1F00' <= char <= '\u1FFF' or      # Greek Extended
        '\u0300' <= char <= '\u036F' or      # Combining Diacritical Marks
        '\u1DC0' <= char <= '\u1DFF' or      # Combining Diacritical Marks Extended
        '\u10140' <= char <= '\u1018F' or    # Ancient Greek Numbers
        '\u1D200' <= char <= '\u1D24F' or    # Greek Musical Notation
        '\u2E00' <= char <= '\u2E7F'         # Supplemental Punctuation
    )
    
    specific_chars = char in {
        '\u03F2', '\u03F9',  # Lunate Sigma
        '\u03D8', '\u03D9',  # Koppa
        '\u03DA', '\u03DB',  # Stigma
        '\u03DC', '\u03DD',  # Digamma
        '\u03E0', '\u03E1'   # Sampi
    }
    
    return basic_ranges or specific_chars

def analyze_single_file(file_path: str) -> Tuple[Counter, Counter, Counter]:
    """
    Analyze a single file and return counters for:
    - Pure Latin words
    - Numbers
    - Greek words containing Latin or numbers
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    latin_word_counter = Counter()
    number_counter = Counter()
    greek_mixed_counter = Counter()

    # Process the text word by word
    words = re.finditer(r'\S+', text)
    for match in words:
        word = match.group()
        
        # Strip punctuation
        clean_word = re.sub(r'^[\s\(\[\{\.,;:]+|[\s\)\]\}\.,;:]+$', '', word)
        if not clean_word:
            continue

        # Check if word contains any Greek characters
        has_greek = any(is_greek_char(c) for c in clean_word)
        
        if has_greek:
            # Check if Greek word contains Latin or numbers
            if re.search(r'[a-zA-Z0-9]', clean_word):
                greek_mixed_counter[clean_word] += 1
        else:
            # Pure number
            if clean_word.isdigit():
                number_counter[clean_word] += 1
            # Latin word (contains at least one Latin letter)
            elif re.search(r'[a-zA-Z]', clean_word):
                latin_word_counter[clean_word.lower()] += 1

    return latin_word_counter, number_counter, greek_mixed_counter

def analyze_greek_texts(folder_path: str) -> Dict[str, Tuple[Counter, Counter, Counter]]:
    """
    Analyze Greek texts and return both per-file and overall statistics.
    """
    file_results = {}
    
    # Process each file
    for file_path in glob.glob(os.path.join(folder_path, "*.txt")):
        latin_counter, number_counter, mixed_counter = analyze_single_file(file_path)
        file_results[file_path] = (latin_counter, number_counter, mixed_counter)
    
    return file_results

def save_frequency_tables(file_results: Dict[str, Tuple[Counter, Counter, Counter]], output_prefix: str):
    """
    Save frequency tables to CSV files.
    """
    # Combine counters from all files
    total_latin = Counter()
    total_numbers = Counter()
    total_mixed = Counter()
    
    for latin_counter, number_counter, mixed_counter in file_results.values():
        total_latin.update(latin_counter)
        total_numbers.update(number_counter)
        total_mixed.update(mixed_counter)
    
    # Save Latin words frequency
    with open(f"{output_prefix}_latin_words.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Word', 'Frequency'])
        writer.writerows(total_latin.most_common())
    
    # Save numbers frequency
    with open(f"{output_prefix}_numbers.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Number', 'Frequency'])
        writer.writerows(total_numbers.most_common())
    
    # Save mixed Greek words frequency
    with open(f"{output_prefix}_greek_mixed.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Word', 'Frequency'])
        writer.writerows(total_mixed.most_common())
    
    # Save per-file statistics
    with open(f"{output_prefix}_per_file_stats.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Latin Words Count', 'Numbers Count', 'Mixed Greek Words Count'])
        for file_path, (latin_counter, number_counter, mixed_counter) in file_results.items():
            writer.writerow([
                os.path.basename(file_path),
                sum(latin_counter.values()),
                sum(number_counter.values()),
                sum(mixed_counter.values())
            ])

def main():
    # Set your input and output paths
    input_folder = "."  # Current directory
    output_prefix = "frequency_analysis"
    
    print("Starting frequency analysis...")
    file_results = analyze_greek_texts(input_folder)
    
    print("Saving results...")
    save_frequency_tables(file_results, output_prefix)
    
    print("Analysis complete. Results saved with prefix:", output_prefix)

if __name__ == "__main__":
    main()

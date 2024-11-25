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
    # Check basic ranges
    basic_ranges = (
        '\u0370' <= char <= '\u03FF' or      # Basic Greek and Coptic
        '\u1F00' <= char <= '\u1FFF' or      # Greek Extended
        '\u0300' <= char <= '\u036F' or      # Combining Diacritical Marks
        '\u1DC0' <= char <= '\u1DFF' or      # Combining Diacritical Marks Extended
        '\u10140' <= char <= '\u1018F' or    # Ancient Greek Numbers
        '\u1D200' <= char <= '\u1D24F' or    # Greek Musical Notation
        '\u2E00' <= char <= '\u2E7F'         # Supplemental Punctuation
    )
    
    # Check specific characters
    specific_chars = char in {
        '\u03F2',  # Lunate Sigma (lowercase)
        '\u03F9',  # Lunate Sigma (uppercase)
        '\u03D8',  # Koppa (uppercase)
        '\u03D9',  # Koppa (lowercase)
        '\u03DA',  # Stigma (uppercase)
        '\u03DB',  # Stigma (lowercase)
        '\u03DC',  # Digamma (uppercase)
        '\u03DD',  # Digamma (lowercase)
        '\u03E0',  # Sampi (uppercase)
        '\u03E1'   # Sampi (lowercase)
    }
    
    return basic_ranges or specific_chars

def is_latin_numeral(s: str) -> bool:
    """
    Check if a string is a Latin numeral, allowing for surrounding punctuation.
    """
    # Strip surrounding punctuation and whitespace
    s = re.sub(r'^[\s\(\[\{\.,;:]+|[\s\)\]\}\.,;:]+$', '', s)
    
    if s == '':
        return False
    
    # Check if the remaining string is a valid Latin numeral
    pattern = r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'
    return bool(re.match(pattern, s.upper()))

def find_longest_streak_with_lines(text: str, greek_words_to_break: int) -> Tuple[int, tuple, Counter]:
    """
    Find the longest streak and its line number range, while counting Latin numerals separately.
    Returns (max_streak, line_range, latin_numeral_counter)
    """
    lines = text.split('\n')
    max_streak = 0
    max_streak_range = (0, 0)
    current_streak = 0
    consecutive_greek_words = 0
    current_start_line = 0
    latin_numeral_counter = Counter()
    
    for i, line in enumerate(lines):
        # First, find and count Latin numerals
        potential_numerals = re.finditer(r'\S+', line)
        for match in potential_numerals:
            word = match.group()
            if is_latin_numeral(word):
                latin_numeral_counter[word] += 1
        
        # Then process streaks, excluding Latin numerals
        words = re.finditer(r'\S+', line)
        
        for match in words:
            word = match.group()
            
            # Skip Latin numerals in streak counting
            if is_latin_numeral(word):
                continue
                
            # Check if word contains any Greek characters
            has_greek = any(is_greek_char(c) for c in word)
            
            if has_greek:
                consecutive_greek_words += 1
                if consecutive_greek_words > greek_words_to_break:
                    if current_streak > max_streak:
                        max_streak = current_streak
                        max_streak_range = (current_start_line, i + 1)
                    current_streak = 0
                    consecutive_greek_words = 1
            else:
                # Check if it's a Latin word
                if re.search(r'[a-zA-Z]', word):
                    if current_streak == 0:
                        current_start_line = i + 1
                    current_streak += 1
                    consecutive_greek_words = 0
    
    # Check final streak
    if current_streak > max_streak:
        max_streak = current_streak
        max_streak_range = (current_start_line, len(lines))
    
    return max_streak, max_streak_range, latin_numeral_counter

def analyze_single_file(file_path: str, greek_words_to_break: int) -> Tuple[Counter, Counter, Counter, Counter, int, tuple]:
    """
    Analyze a single file and return its counters, streak length, and streak line range.
    """
    latin_word_counter = Counter()
    number_counter = Counter()
    greek_mixed_counter = Counter()
    latin_numeral_counter = Counter()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            
            # Find Latin sequences with their surrounding context
            latin_matches = re.finditer(r'(.?)([a-zA-Z]+)(.?)', text)
            number_matches = re.finditer(r'(.?)(\d+)(.?)', text)
            
            # Process Latin matches (excluding Latin numerals)
            for match in latin_matches:
                prev_char, latin_seq, next_char = match.groups()
                full_word = f"{prev_char}{latin_seq}{next_char}".strip()
                
                # Skip if it's a Latin numeral
                if is_latin_numeral(full_word):
                    continue
                    
                has_greek_neighbor = (prev_char and is_greek_char(prev_char)) or (next_char and is_greek_char(next_char))
                
                if has_greek_neighbor:
                    greek_mixed_counter[full_word] += 1
                else:
                    if full_word:
                        latin_word_counter[full_word] += 1
            
            # Process number matches
            for match in number_matches:
                prev_char, number_seq, next_char = match.groups()
                has_greek_neighbor = (prev_char and is_greek_char(prev_char)) or (next_char and is_greek_char(next_char))
                full_word = f"{prev_char}{number_seq}{next_char}".strip()
                
                if has_greek_neighbor:
                    greek_mixed_counter[full_word] += 1
                else:
                    if full_word:
                        number_counter[full_word] += 1
            
            # Find longest streak and its line range, plus Latin numerals
            longest_streak, line_range, file_latin_numerals = find_longest_streak_with_lines(text, greek_words_to_break)
            latin_numeral_counter.update(file_latin_numerals)
                    
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return Counter(), Counter(), Counter(), Counter(), 0, (0, 0)
    
    return latin_word_counter, number_counter, greek_mixed_counter, latin_numeral_counter, longest_streak, line_range

def analyze_greek_texts(folder_path: str, greek_words_to_break: int) -> Tuple[Dict[str, Tuple[Counter, Counter, Counter, Counter, int, tuple]], Counter, Counter, Counter, Counter]:
    """
    Analyze Greek texts and return both per-file and overall statistics.
    """
    total_latin_counter = Counter()
    total_number_counter = Counter()
    total_greek_mixed_counter = Counter()
    total_latin_numeral_counter = Counter()
    file_results = {}
    
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    
    for file_path in txt_files:
        print(f"Processing file: {os.path.basename(file_path)}")
        results = analyze_single_file(file_path, greek_words_to_break)
        file_results[file_path] = results
        
        latin_counter, number_counter, greek_mixed_counter, latin_numeral_counter, _, _ = results
        total_latin_counter.update(latin_counter)
        total_number_counter.update(number_counter)
        total_greek_mixed_counter.update(greek_mixed_counter)
        total_latin_numeral_counter.update(latin_numeral_counter)
    
    return file_results, total_latin_counter, total_number_counter, total_greek_mixed_counter, total_latin_numeral_counter

def save_regular_results(latin_word_counter, number_counter, latin_numeral_counter, output_file):
    """
    Save the pure Latin words, numbers, and Latin numerals to a CSV file.
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Item', 'Type', 'Frequency'])
        
        # Write Latin word frequencies
        for word, freq in sorted(latin_word_counter.items()):
            writer.writerow([word, 'Latin_Word', freq])
            
        # Write number frequencies
        for num, freq in sorted(number_counter.items()):
            writer.writerow([num, 'Number', freq])
            
        # Write Latin numeral frequencies
        for numeral, freq in sorted(latin_numeral_counter.items()):
            writer.writerow([numeral, 'Latin_Numeral', freq])

def save_mixed_results(greek_mixed_counter, output_file):
    """
    Save the Greek words containing Latin chars or numbers to a CSV file.
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Mixed_Word', 'Frequency', 'Contains_Latin', 'Contains_Numbers'])
        
        for word, freq in sorted(greek_mixed_counter.items()):
            has_latin = 'Yes' if re.search(r'[a-zA-Z]', word) else 'No'
            has_numbers = 'Yes' if re.search(r'\d', word) else 'No'
            writer.writerow([word, freq, has_latin, has_numbers])

def save_file_statistics(file_results: Dict[str, Tuple[Counter, Counter, Counter, Counter, int, tuple]], output_file: str, greek_words_to_break: int):
    """
    Save per-file statistics to a CSV file with streak line ranges.
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Filename',
            'Total Latin Words',
            'Total Numbers',
            'Total Mixed Greek Words',
            'Total Latin Numerals',
            f'Longest Streak (Break after {greek_words_to_break} Greek words)',
            'Streak Line Range'
        ])
        
        for file_path, (latin_counter, number_counter, greek_mixed_counter, latin_numeral_counter, longest_streak, line_range) in file_results.items():
            writer.writerow([
                os.path.basename(file_path),
                sum(latin_counter.values()),
                sum(number_counter.values()),
                sum(greek_mixed_counter.values()),
                sum(latin_numeral_counter.values()),
                longest_streak,
                f"{line_range[0]}-{line_range[1]}" if longest_streak > 0 else "N/A"
            ])

def main():
    folder_path = os.getcwd()
    regular_output = "latin_numeral_count.csv"
    mixed_output = "greek_words_with_char-numeral.csv"
    
    # Define break parameters for different analyses
    break_params = {
        'strict': 0,    # Any Greek word breaks the streak
        'tolerant': 2   # More than 2 consecutive Greek words needed to break streak
    }
    
    print(f"Analyzing text files in: {folder_path}")
    
    # Run analysis for each break parameter
    for param_name, break_value in break_params.items():
        stats_output = f"file_statistics_{param_name}.csv"
        
        # Analyze texts with current break parameter
        file_results, total_latin_counter, total_number_counter, total_greek_mixed_counter, total_latin_numeral_counter = \
            analyze_greek_texts(folder_path, break_value)
        
        # Save statistics for current parameter
        save_file_statistics(file_results, stats_output, break_value)
        
        # Only save these once (they're the same for both analyses)
        if param_name == 'strict':
            save_regular_results(total_latin_counter, total_number_counter, total_latin_numeral_counter, regular_output)
            save_mixed_results(total_greek_mixed_counter, mixed_output)
        
        print(f"Saved {param_name} analysis to {stats_output}")
    
    print("\nAnalysis complete. Files created:")
    print(f"- {regular_output} (overall Latin words, numbers, and Latin numerals)")
    print(f"- {mixed_output} (overall Greek words with Latin/numbers)")
    for param_name in break_params:
        print(f"- file_statistics_{param_name}.csv (per-file statistics)")

if __name__ == "__main__":
    main()
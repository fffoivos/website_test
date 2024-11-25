import os
import re
from typing import List, Tuple
import glob

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
    
    # Check if the remaining string is a valid Latin numeral
    pattern = r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'
    return bool(re.match(pattern, s.upper()))

def find_streaks_in_text(text: str, greek_words_to_break: int = 1) -> List[Tuple[int, int, List[str]]]:
    """
    Find all streaks of non-Greek text and their line ranges.
    Returns list of tuples: (start_line, end_line, words_in_streak)
    """
    lines = text.split('\n')
    streaks = []
    current_streak = []
    current_start_line = 0
    consecutive_greek_words = 0
    
    for i, line in enumerate(lines, 1):
        words = re.finditer(r'\S+', line)
        
        for match in words:
            word = match.group()
            
            # Check if word contains any Greek characters
            has_greek = any(is_greek_char(c) for c in word)
            
            if has_greek:
                consecutive_greek_words += 1
                if consecutive_greek_words > greek_words_to_break:
                    if current_streak:
                        streaks.append((current_start_line, i, current_streak.copy()))
                        current_streak = []
                    consecutive_greek_words = 1
            else:
                # Check if it's a Latin word or numeral
                if re.search(r'[a-zA-Z]', word) or re.search(r'\d', word) or is_latin_numeral(word):
                    if not current_streak:
                        current_start_line = i
                    current_streak.append(word)
                    consecutive_greek_words = 0
    
    # Add final streak if exists
    if current_streak:
        streaks.append((current_start_line, len(lines), current_streak))
    
    return streaks

def analyze_file_streaks(file_path: str, threshold: int = 5) -> Tuple[List[Tuple[int, int, List[str]]], List[Tuple[int, int, List[str]]]]:
    """
    Analyze a single file and return two lists of streaks:
    1. Streaks with length <= threshold
    2. Streaks with length > threshold
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            all_streaks = find_streaks_in_text(text)
            
            shorter_streaks = []
            longer_streaks = []
            
            for streak in all_streaks:
                if len(streak[2]) <= threshold:
                    shorter_streaks.append(streak)
                else:
                    longer_streaks.append(streak)
            
            return shorter_streaks, longer_streaks
            
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return [], []

def create_streak_report(filename: str, shorter_streaks: List[Tuple[int, int, List[str]]], 
                        longer_streaks: List[Tuple[int, int, List[str]]], threshold: int) -> str:
    """
    Create a formatted report of the streaks found in a file.
    """
    report = [f"Streak Analysis for: {filename}\n"]
    
    # Report shorter streaks
    report.append(f"\nShort Streaks (length <= {threshold}):")
    if shorter_streaks:
        for start, end, words in shorter_streaks:
            report.append(f"\nLines {start}-{end}: {' '.join(words)}")
    else:
        report.append("\nNo short streaks found.")
    
    # Report longer streaks
    report.append(f"\n\nLong Streaks (length > {threshold}):")
    if longer_streaks:
        for start, end, words in longer_streaks:
            report.append(f"\nLines {start}-{end} [{len(words)} words]: {' '.join(words)}")
    else:
        report.append("\nNo long streaks found.")
    
    return '\n'.join(report)

def clean_text_from_streaks(text: str, longer_streaks: List[Tuple[int, int, List[str]]]) -> str:
    """
    Remove all sequences from the text based on the identified streaks.
    """
    lines = text.split('\n')
    # Create a set of line numbers to remove
    lines_to_remove = set()
    for start, end, _ in longer_streaks:
        lines_to_remove.update(range(start-1, end))  # -1 because line numbers are 1-based
    
    # Keep only lines that are not in the removal set
    cleaned_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
    return '\n'.join(cleaned_lines)

def process_directory(input_dir: str, output_dir: str, threshold: int = 5, mode: str = "analysis"):
    """
    Process all txt files in input directory.
    mode: "analysis" creates reports, "clean" removes sequences and saves cleaned files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each txt file
    for txt_file in glob.glob(os.path.join(input_dir, "*.txt")):
        filename = os.path.basename(txt_file)
        print(f"Processing: {filename}")
        
        # Analyze streaks
        shorter_streaks, longer_streaks = analyze_file_streaks(txt_file, threshold)
        
        if mode == "analysis":
            # Create and save report
            if shorter_streaks or longer_streaks:
                report = create_streak_report(filename, shorter_streaks, longer_streaks, threshold)
                output_path = os.path.join(output_dir, filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
        else:  # mode == "clean"
            # Read the original text
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Clean the text
            cleaned_text = clean_text_from_streaks(text, longer_streaks)
            
            # Save the cleaned text
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)

def main():
    # Configuration
    input_directory = os.getcwd()
    mode = "clean" # "analysis" or "clean"
    output_directory = "latin_analysis" if mode == "analysis" else "cleaned_files"
    threshold = 0  # Default threshold for separating short and long streaks
    
    print(f"Processing texts from: {input_directory}")
    print(f"Mode: {mode}")
    print(f"Saving {'reports' if mode == 'analysis' else 'cleaned files'} to: {output_directory}")
    
    process_directory(input_directory, output_directory, threshold, mode)
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
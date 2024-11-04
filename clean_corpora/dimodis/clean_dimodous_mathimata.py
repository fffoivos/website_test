import os
import re
from typing import List, Tuple, Dict, NamedTuple

class TextRange(NamedTuple):
    start: int  # Line number start
    end: int    # Line number end
    tag: str    # Tag to apply

def find_page_marker_ranges(lines: List[str]) -> List[TextRange]:
    """Find ranges for page markers"""
    ranges = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == '=' * 20:
            if i + 2 < len(lines) and lines[i + 2].strip() == '=' * 20:
                ranges.append(TextRange(i, i + 2, '[σελ]'))
                i += 2
        i += 1
    return ranges

def find_introduction_range(lines: List[str]) -> List[TextRange]:
    """Find range for introduction section"""
    ranges = []
    end_line = -1
    
    for i, line in enumerate(lines):
        if "Β. ΣΥΝΤΟΜΗ ΠΕΡΙΓΡΑΦΗ/ΠΕΡΙΛΗΨΗ" in line:
            end_line = i - 1
            break
    
    if end_line >= 0:
        ranges.append(TextRange(0, end_line, '[ΕΙΣΑΓΩΓΗ]'))
    return ranges

def find_bibliography_range(lines: List[str]) -> List[TextRange]:
    """Find range for bibliography section"""
    ranges = []
    start_line = -1
    end_line = -1
    
    for i, line in enumerate(lines):
        if "Θ. ΒΙΒΛΙΟΓΡΑΦΙΑ" in line:
            start_line = i
        elif start_line != -1 and "ΠΑΡΑΡΤΗΜΑ" in line:
            end_line = i - 1
            break
    
    if start_line >= 0 and end_line >= 0:
        ranges.append(TextRange(start_line, end_line, '[ΒΙΒΛ]'))
    return ranges

def find_contents_range(lines: List[str]) -> List[TextRange]:
    """Find range for contents section"""
    ranges = []
    start_line = -1
    end_line = -1
    
    for i, line in enumerate(lines):
        if "Κείμενα" in line:
            start_line = i
        elif start_line != -1 and "Διδακτική πορεία" in line:
            end_line = i - 1
            break
    
    if start_line >= 0 and end_line >= 0:
        ranges.append(TextRange(start_line, end_line, '[ΠΙΝΑΞ]'))
    return ranges

def find_all_ranges(lines: List[str]) -> List[TextRange]:
    """Collect all ranges that need to be processed"""
    ranges = []
    ranges.extend(find_page_marker_ranges(lines))
    ranges.extend(find_introduction_range(lines))
    ranges.extend(find_bibliography_range(lines))
    ranges.extend(find_contents_range(lines))
    return ranges

def is_section_header(line: str) -> bool:
    """Check if a line is a section header"""
    return bool(re.match(r'^[ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]\. [ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ\s/]+$', line.strip()))

def is_caps_line(line: str) -> bool:
    """Check if a line is all uppercase"""
    return bool(line.strip() and line.strip().isupper())

def process_lines(lines: List[str], ranges: List[TextRange], remove_mode: bool) -> List[str]:
    """Process lines based on ranges and mode"""
    processed_lines = []
    
    i = 0
    while i < len(lines):
        current_line = lines[i].rstrip()
        
        # Get next line if available
        next_line = lines[i + 1].rstrip() if i + 1 < len(lines) else ""
        
        # Check if current line is empty
        if not current_line:
            i += 1
            continue
            
        # Check if next line is a section header or all caps
        next_is_section = is_section_header(next_line)
        next_is_caps = is_caps_line(next_line)
        
        # Check if line is in any range
        line_tags = []
        should_process = False
        for range_item in ranges:
            if range_item.start <= i <= range_item.end:
                should_process = True
                if not remove_mode:
                    line_tags.append(range_item.tag)
        
        # Process the current line
        if should_process:
            if not remove_mode:
                processed_lines.append(f"{' '.join(line_tags)} {current_line}")
        else:
            processed_lines.append(current_line)
            
            # Add empty line before section headers or caps lines
            if next_is_section or next_is_caps:
                processed_lines.append("")
        
        i += 1
    
    return processed_lines

def process_file(file_path: str, remove_mode: bool) -> List[str]:
    """Process a single file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    ranges = find_all_ranges(lines)
    return process_lines(lines, ranges, remove_mode)

def process_folder(folder_path: str, remove_mode: bool):
    """Process all txt files in a folder"""
    if not os.path.exists(folder_path):
        raise Exception(f"Folder path {folder_path} does not exist")
    
    output_dir = os.path.join(folder_path, "processed_files")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    files_processed = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            try:
                file_path = os.path.join(folder_path, filename)
                processed_lines = process_file(file_path, remove_mode)
                
                output_path = os.path.join(output_dir, filename)
                with open(output_path, 'w', encoding='utf-8') as file:
                    for line in processed_lines:
                        file.write(line + '\n')
                
                files_processed += 1
                print(f"Successfully processed {filename}")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nProcessing complete!")
    print(f"Files processed: {files_processed}")

# Example usage
if __name__ == "__main__":
    folder_path = "/home/fivos/Desktop/text_sources/dimodis/dimodis_lesson_texts"
    
    # Set to True to remove matched ranges, False to tag them
    remove_mode = True
    
    process_folder(folder_path, remove_mode)
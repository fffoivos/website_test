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
        if "Β. ΣΥΝΤΟΜΗ ΠΕΡΙΓΡΑΦΗ/ΠΕΡΙΛΗΨΗ" in line or "Β. ΣΎΝΤΟΜΗ ΠΕΡΙΓΡΑΦΗ/ΠΕΡΙΛΗΨΗ" in line:
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

def should_remove_line(line: str) -> bool:
    """Check if line should be removed based on specific patterns"""
    # Check for MIS pattern
    if re.search(r'MIS:\s*\d+', line):
        return True
    
    # Check for Π x x x pattern
    if re.match(r'Π\s+\d+\s+\d+\s+\d+:', line):
        return True
    
    # Check for ΚΕΝΤΡΟ ΕΛΛΗΝΙΚΗΣ ΓΛΩΣΣΑΣ
    if line.strip() == "ΚΕΝΤΡΟ ΕΛΛΗΝΙΚΗΣ ΓΛΩΣΣΑΣ":
        return True
    
    return False

def process_lines(lines: List[str], ranges: List[TextRange], remove_mode: bool) -> List[str]:
    """Process lines based on ranges and mode"""
    temp_lines = []  # Temporary storage for lines being processed
    i = 0
    
    while i < len(lines):
        current_line = lines[i].rstrip()
        
        # Check for KEG pattern and surrounding empty lines
        if current_line.strip() == "ΚΕΝΤΡΟ ΕΛΛΗΝΙΚΗΣ ΓΛΩΣΣΑΣ":
            # Remove previous empty lines
            while temp_lines and not temp_lines[-1].strip():
                temp_lines.pop()
            # Skip current line and following empty lines
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue
        
        # Skip other lines that match removal patterns
        if should_remove_line(current_line):
            i += 1
            continue
        
        # Replace private-use character with bullet
        current_line = current_line.replace('\uf0a7', '•')
        
        # Check if current line is a section header or caps
        is_header = is_section_header(current_line) or is_caps_line(current_line)
        
        # Check if line is in any range
        line_tags = []
        should_process = False
        for range_item in ranges:
            if range_item.start <= i <= range_item.end:
                should_process = True
                if not remove_mode:
                    line_tags.append(range_item.tag)
        
        if should_process and remove_mode:
            i += 1
            continue
        
        # Handle line addition with proper spacing
        if current_line:  # Only process non-empty lines
            # Add blank line before header if needed
            if is_header and (not temp_lines or temp_lines[-1] != ""):
                temp_lines.append("")
            
            # Add the current line with tags if needed
            if not remove_mode:
                # Add [ΓΡΑΜ] tag if not in remove mode
                tags = ['[ΓΡΑΜ]'] + line_tags if line_tags else ['[ΓΡΑΜ]']
                temp_lines.append(f"{' '.join(tags)} {current_line}")
            else:
                temp_lines.append(current_line)
            
            # Add blank line after header if needed
            if is_header:
                temp_lines.append("")
        
        # Move to next line
        i += 1
    
    # Remove duplicate blank lines and return
    return remove_duplicate_blank_lines(temp_lines)

def remove_duplicate_blank_lines(lines: List[str]) -> List[str]:
    """Remove duplicate blank lines from the processed text"""
    result = []
    prev_empty = False
    
    for line in lines:
        is_empty = not line.strip()
        if not is_empty or not prev_empty:
            result.append(line)
        prev_empty = is_empty
    
    # Remove trailing empty lines
    while result and not result[-1].strip():
        result.pop()
        
    return result

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
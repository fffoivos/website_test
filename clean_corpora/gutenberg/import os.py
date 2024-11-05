import os
from pathlib import Path
import shutil
from itertools import combinations
from typing import List, Dict, Set, Tuple
import numpy as np

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def read_text_files(folder_path: str) -> Dict[str, str]:
    """Read all text files from the given folder."""
    text_files = {}
    for file in Path(folder_path).glob('*.txt'):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                text_files[file.name] = f.read()
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return text_files

def find_similar_groups(texts: Dict[str, str], threshold: int) -> List[Set[str]]:
    """Find groups of similar texts based on Levenshtein distance."""
    groups = []
    processed = set()
    
    # Calculate distances between all pairs
    file_names = list(texts.keys())
    for i, j in combinations(range(len(file_names)), 2):
        file1, file2 = file_names[i], file_names[j]
        
        if file1 in processed or file2 in processed:
            continue
            
        distance = levenshtein_distance(texts[file1], texts[file2])
        
        if distance <= threshold:
            # Check if either file belongs to an existing group
            found_group = False
            for group in groups:
                if file1 in group or file2 in group:
                    group.add(file1)
                    group.add(file2)
                    found_group = True
                    break
            
            if not found_group:
                # Create new group
                groups.append({file1, file2})
            
            processed.add(file1)
            processed.add(file2)
    
    return groups

def organize_files(input_path: str, threshold: int) -> str:
    """Main function to organize text files based on similarity."""
    # Read all text files
    texts = read_text_files(input_path)
    if not texts:
        raise ValueError("No text files found in the specified directory")
    
    # Create output directory
    output_path = os.path.join(input_path, "organized_texts")
    os.makedirs(output_path, exist_ok=True)
    
    # Find similar groups
    similar_groups = find_similar_groups(texts, threshold)
    
    # Create directory structure and move files
    for i, group in enumerate(similar_groups, 1):
        # Create group directory
        group_dir = os.path.join(output_path, f"group_{i}")
        os.makedirs(group_dir, exist_ok=True)
        
        # Move files to group directory
        for filename in group:
            src = os.path.join(input_path, filename)
            dst = os.path.join(group_dir, filename)
            shutil.copy2(src, dst)
    
    # Handle ungrouped files
    all_grouped_files = {file for group in similar_groups for file in group}
    ungrouped_files = set(texts.keys()) - all_grouped_files
    
    if ungrouped_files:
        ungrouped_dir = os.path.join(output_path, "ungrouped")
        os.makedirs(ungrouped_dir, exist_ok=True)
        for filename in ungrouped_files:
            src = os.path.join(input_path, filename)
            dst = os.path.join(ungrouped_dir, filename)
            shutil.copy2(src, dst)
    
    return output_path

# Example usage
if __name__ == "__main__":
    input_path = "path/to/your/text/files"
    threshold = 50  # Adjust this value based on your needs
    try:
        output_path = organize_files(input_path, threshold)
        print(f"Files organized successfully in: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
import os
from pathlib import Path
import shutil
from itertools import combinations
from typing import List, Dict, Set, Tuple
import numpy as np
from multiprocessing import Pool, cpu_count, Manager
import time
from functools import partial
from tqdm import tqdm
import math

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

def read_file(args):
    """Read a single file with line limit. Used for parallel processing."""
    filepath, max_lines = args
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return (filepath.name, ''.join(lines))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def read_text_files_parallel(folder_path: str, max_lines: int = 500) -> Dict[str, str]:
    """Read files in parallel using multiple processes."""
    print(f"\n1. Reading text files in parallel (first {max_lines} lines only):")
    print("-" * 50)
    
    files = list(Path(folder_path).glob('*.txt'))
    print(f"Found {len(files)} files to process")
    
    # Create arguments for parallel processing
    args = [(f, max_lines) for f in files]
    
    # Use number of CPU cores or number of files, whichever is smaller
    n_cores = min(cpu_count(), len(files))
    print(f"Using {n_cores} CPU cores for parallel processing")
    
    start_time = time.time()
    text_files = {}
    
    with Pool(n_cores) as pool:
        # Use tqdm to create a progress bar
        with tqdm(total=len(files), desc="Reading files") as pbar:
            for result in pool.imap_unordered(read_file, args):
                if result:
                    text_files[result[0]] = result[1]
                pbar.update()
    
    duration = time.time() - start_time
    print(f"\nTotal files read: {len(text_files)}")
    print(f"Reading time: {duration:.2f} seconds")
    
    return text_files

def compare_pair(args):
    """Compare a pair of texts. Used for parallel processing."""
    (file1, text1), (file2, text2), threshold = args
    distance = levenshtein_distance(text1, text2)
    return (file1, file2, distance <= threshold, distance)

def find_similar_groups_parallel(texts: Dict[str, str], threshold: int) -> List[Set[str]]:
    """Find groups of similar texts using parallel processing."""
    print("\n2. Analyzing text similarities in parallel:")
    print("-" * 50)
    
    # Create all possible pairs for comparison
    items = list(texts.items())
    pairs = []
    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items[i+1:], i+1):
            pairs.append((item1, item2, threshold))
    
    total_comparisons = len(pairs)
    print(f"Total comparisons to make: {total_comparisons}")
    
    # Use number of CPU cores or number of comparisons, whichever is smaller
    n_cores = min(cpu_count(), total_comparisons)
    print(f"Using {n_cores} CPU cores for parallel processing")
    
    # Initialize counters for progress reporting
    similar_count = 0
    processed_count = 0
    
    start_time = time.time()
    groups = []
    processed = set()
    
    with Pool(n_cores) as pool:
        # Use tqdm to create a progress bar
        with tqdm(total=total_comparisons, desc="Comparing files") as pbar:
            for file1, file2, is_similar, distance in pool.imap_unordered(compare_pair, pairs):
                if is_similar and file1 not in processed and file2 not in processed:
                    similar_count += 1
                    # Check if either file belongs to an existing group
                    found_group = False
                    for group in groups:
                        if file1 in group or file2 in group:
                            group.add(file1)
                            group.add(file2)
                            found_group = True
                            break
                    
                    if not found_group:
                        groups.append({file1, file2})
                    
                    processed.add(file1)
                    processed.add(file2)
                    
                    # Update progress description with similarity information
                    pbar.set_postfix(similar_pairs=similar_count, 
                                   groups=len(groups), 
                                   last_distance=distance)
                
                processed_count += 1
                pbar.update()
    
    duration = time.time() - start_time
    print(f"\nComparison time: {duration:.2f} seconds")
    print(f"Found {similar_count} similar pairs in {len(groups)} groups")
    
    return groups

def organize_files(input_path: str, threshold: int, max_lines: int = 500) -> str:
    """Main function to organize text files based on similarity."""
    print(f"\nStarting organization process:")
    print(f"- Threshold: {threshold}")
    print(f"- Analyzing first {max_lines} lines of each file")
    print(f"- Using parallel processing with {cpu_count()} CPU cores")
    print("=" * 50)
    
    start_time = time.time()
    
    # Read all text files in parallel
    texts = read_text_files_parallel(input_path, max_lines)
    if not texts:
        raise ValueError("No text files found in the specified directory")
    
    # Create output directory
    output_path = os.path.join(input_path, "organized_texts")
    os.makedirs(output_path, exist_ok=True)
    print(f"\nCreated output directory: {output_path}")
    
    # Find similar groups using parallel processing
    similar_groups = find_similar_groups_parallel(texts, threshold)
    
    # Create directory structure and copy files
    print("\n3. Copying files to new structure:")
    print("-" * 50)
    
    # Get total number of files to copy
    total_files = sum(len(group) for group in similar_groups)
    copied_files = 0
    
    with tqdm(total=total_files, desc="Copying grouped files") as pbar:
        for i, group in enumerate(similar_groups, 1):
            # Create group directory
            group_dir = os.path.join(output_path, f"group_{i}")
            os.makedirs(group_dir, exist_ok=True)
            
            # Copy files to group directory
            for filename in group:
                src = os.path.join(input_path, filename)
                dst = os.path.join(group_dir, filename)
                shutil.copy2(src, dst)
                copied_files += 1
                pbar.update()
                pbar.set_postfix(group=i, files_in_group=len(group))
    
    # Handle ungrouped files
    all_grouped_files = {file for group in similar_groups for file in group}
    ungrouped_files = set(texts.keys()) - all_grouped_files
    
    if ungrouped_files:
        ungrouped_dir = os.path.join(output_path, "ungrouped")
        os.makedirs(ungrouped_dir, exist_ok=True)
        
        with tqdm(total=len(ungrouped_files), desc="Copying ungrouped files") as pbar:
            for filename in ungrouped_files:
                src = os.path.join(input_path, filename)
                dst = os.path.join(ungrouped_dir, filename)
                shutil.copy2(src, dst)
                pbar.update()
    
    total_duration = time.time() - start_time
    print("\nOrganization complete!")
    print(f"Processed {len(texts)} files:")
    print(f"- Created {len(similar_groups)} groups")
    print(f"- {len(ungrouped_files)} files remained ungrouped")
    print(f"Total processing time: {total_duration:.2f} seconds")
    
    # Calculate and display processing speed
    files_per_second = len(texts) / total_duration
    print(f"Processing speed: {files_per_second:.2f} files/second")
    
    return output_path

# Example usage
if __name__ == "__main__":
    input_path = "/media/fivos/247968ad-2d9f-4d34-839a-ebc33dff1531/gutenberg_clean/"
    threshold = 50  # Adjust this value based on your needs
    max_lines = 500  # Maximum number of lines to analyze per file
    
    try:
        output_path = organize_files(input_path, threshold, max_lines)
        print(f"\nFiles organized successfully in: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
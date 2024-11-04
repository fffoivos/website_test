import unicodedata
import re
from collections import defaultdict
import pandas as pd

def normalize_text(text):
    """
    Normalize the text by:
    - Converting to lowercase
    - Removing accents
    - Replacing multiple whitespace with a single space
    - Stripping leading and trailing whitespace
    """
    text = text.lower()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def levenshtein_distance(s1, s2, max_distance):
    """
    Compute the Levenshtein distance between two strings.
    Stops early if the distance exceeds max_distance.
    """
    if abs(len(s1) - len(s2)) > max_distance:
        return max_distance + 1
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        min_distance_in_row = current_row[0]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1    
            deletions = current_row[j] + 1          
            substitutions = previous_row[j] + (c1 != c2)
            current_cell = min(insertions, deletions, substitutions)
            current_row.append(current_cell)
            min_distance_in_row = min(min_distance_in_row, current_cell)
        if min_distance_in_row > max_distance:
            return max_distance + 1
        previous_row = current_row
    return previous_row[-1]

class BKTree:
    """
    BK-Tree implementation for efficient similarity search.
    """
    def __init__(self, distance_func):
        self.tree = None
        self.distance_func = distance_func

    def add(self, item, max_distance=3):
        if self.tree is None:
            self.tree = ([item], {})
            return
        node_items, children = self.tree
        distance = self.distance_func(item, node_items[0], max_distance)
        if distance == 0:
            node_items.append(item)
        elif distance <= max_distance:
            if distance in children:
                children[distance].add(item, max_distance)
            else:
                children[distance] = BKTree(self.distance_func)
                children[distance].tree = ([item], {})
        # Items with distance > max_distance are not added

    def search(self, item, max_distance):
        results = []
        if self.tree is None:
            return results
        node_items, children = self.tree
        distance = self.distance_func(item, node_items[0], max_distance)
        if distance <= max_distance:
            results.extend(node_items)
        for dist in range(distance - max_distance, distance + max_distance + 1):
            if dist < 0:
                continue
            child = children.get(dist)
            if child is not None:
                results.extend(child.search(item, max_distance))
        return results

def remove_duplicates(csv_path, output_path, max_distance=3):
    """
    Reads a CSV file, removes duplicate or similar entries in the 'text' column based on similarity,
    and exports the cleaned DataFrame to a new CSV file.

    Parameters:
    - csv_path: Path to the input CSV file.
    - output_path: Path to save the cleaned CSV file without duplicates.
    - max_distance: Maximum Levenshtein distance to consider entries as duplicates.
    """
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: File not found - {csv_path}")
        return
    except pd.errors.EmptyDataError:
        print("Error: CSV file is empty.")
        return
    except pd.errors.ParserError:
        print("Error: Error parsing CSV file.")
        return

    # Ensure 'text' column exists
    if 'text' not in df.columns:
        print("Error: CSV does not contain a 'text' column.")
        return

    # Normalize the 'text' column
    print("Normalizing text data...")
    df['normalized_text'] = df['text'].astype(str).apply(normalize_text)

    # Initialize BKTree with the Levenshtein distance function
    print("Initializing BK-Tree...")
    bk_tree = BKTree(lambda a, b, max_dist: levenshtein_distance(a, b, max_dist))

    # Dictionary to hold groups of similar entries
    similar_groups = defaultdict(list)

    # Iterate over the DataFrame to build similar groups
    print("Building groups of similar entries...")
    for index, row in df.iterrows():
        text = row['normalized_text']
        matches = bk_tree.search(text, max_distance)
        if matches:
            # Assign to the first matching group
            similar_text = matches[0]
            similar_groups[similar_text].append(index)
        else:
            # Create a new group
            bk_tree.add(text, max_distance)
            similar_groups[text].append(index)

    # Collect duplicates (excluding the first occurrence in each group)
    print("Identifying duplicates...")
    duplicate_indices = []
    for group_text, indices in similar_groups.items():
        if len(indices) > 1:
            # Exclude the first occurrence
            duplicate_indices.extend(indices[1:])

    if duplicate_indices:
        print(f"Found {len(duplicate_indices)} duplicate(s). Removing duplicates...")
        # Remove duplicates from the DataFrame
        cleaned_df = df.drop(index=duplicate_indices).reset_index(drop=True)
        # Drop the 'normalized_text' column as it's no longer needed
        cleaned_df = cleaned_df.drop(columns=['normalized_text'])
        try:
            # Export the cleaned DataFrame to a new CSV file
            cleaned_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"Cleaned data has been exported to {output_path}")
        except Exception as e:
            print(f"Error: Failed to export cleaned data to CSV - {e}")
    else:
        print("No duplicates found. No changes made to the dataset.")

if __name__ == "__main__":
    # Replace 'input.csv' with your actual CSV file path
    input_csv_path = '/home/fivos/sxolika_dataset.csv'
    # Specify the output CSV file path
    output_csv_path = '/home/fivos/sxolika_dataset.csv'
    # Optionally, adjust the max_distance as needed
    max_lev_distance = 3
    remove_duplicates(input_csv_path, output_csv_path, max_distance=max_lev_distance)
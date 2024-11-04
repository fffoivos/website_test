import os
import re

# Keep your existing REPLACEMENTS dictionary
REPLACEMENTS = {
    "auctorm": "auctores",
    "autorum": "auctores",
    "chap0ter": "chapter",
    "chapterer": "chapter",
    "chaptser": "chapter",
    "chaspter": "chapter",
    " chapter": "chapter",
    "chapter1": "chapter",
    "sction": "section",
    "sectionn": "section",
    "setion": "section",
    "subdsection": "subsection",
    "subection": "subsection",
    " section": "section",
    "setence": "sentence"
}

def process_file(file_path):
    """Process a single XML file and apply the replacements."""
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if any changes were made
        changes_made = False
        
        # For each possible replacement
        for old_value, new_value in REPLACEMENTS.items():
            # Look specifically for subtype attributes with this value
            pattern = f'subtype="{old_value}"'
            replacement = f'subtype="{new_value}"'
            
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes_made = True
                print(f"In {file_path}: replaced '{old_value}' with '{new_value}'")
            
            # Also check for single-quoted attributes
            pattern = f"subtype='{old_value}'"
            replacement = f"subtype='{new_value}'"
            
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes_made = True
                print(f"In {file_path}: replaced '{old_value}' with '{new_value}'")
        
        # Only write the file if changes were made
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return False

# Keep your existing process_directory and main functions as they are
def process_directory(root_dir):
    """Process all XML files in the directory structure."""
    files_processed = 0
    files_modified = 0
    
    for first_level_dir in os.listdir(root_dir):
        first_level_path = os.path.join(root_dir, first_level_dir)
        if not os.path.isdir(first_level_path):
            continue
            
        for second_level_dir in os.listdir(first_level_path):
            second_level_path = os.path.join(first_level_path, second_level_dir)
            if not os.path.isdir(second_level_path):
                continue
                
            for filename in os.listdir(second_level_path):
                if filename.startswith("__") or not filename.endswith(".xml"):
                    continue
                    
                file_path = os.path.join(second_level_path, filename)
                files_processed += 1
                
                if process_file(file_path):
                    files_modified += 1
                    print(f"Modified: {file_path}")
                
                if files_processed % 100 == 0:
                    print(f"Processed {files_processed} files...")
    
    return files_processed, files_modified

def main():
    # Replace this path with your actual path
    root_directory = "/home/fivos/Desktop/First1KGreek/data"
    
    # Process all files
    print("Starting processing...")
    files_processed, files_modified = process_directory(root_directory)
    
    # Print summary
    print("\nProcessing complete!")
    print(f"Total files processed: {files_processed}")
    print(f"Files modified: {files_modified}")

if __name__ == "__main__":
    main()
import json
import os
import shutil

# Paths and file names
base_path = "/home/fivos/Desktop/ebooks/pymu_pdf"
sync_json_name = "progress_report.json"
output_json_name = "filter_out_text.json"
filtered_out_folder = os.path.join(base_path, "Filtered_out_of_JSON")

# Ensure the filtered out folder exists
os.makedirs(filtered_out_folder, exist_ok=True)

# Full paths for reading and writing
prototype_json_path = "/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_by_JSON/filtered_out_extracted_files.JSON"
sync_json_path = os.path.join(base_path, sync_json_name)
output_json_path = os.path.join(base_path, output_json_name)

# Load JSON data
with open(prototype_json_path, 'r', encoding='utf-8') as file:
    prototype_data = json.load(file)

with open(sync_json_path, 'r', encoding='utf-8') as file:
    sync_data = json.load(file)

# Find values in the prototype
prototype_values = set(prototype_data.values())

# Filter the target JSON to keep only key-value pairs with matching values
filtered_sync_data = {key: value for key, value in sync_data.items() if value in prototype_values}

# Write the filtered data to a new JSON file
with open(output_json_path, 'w', encoding='utf-8') as file:
    json.dump(filtered_sync_data, file, ensure_ascii=False, indent=4)

# Read all .txt files in the base path
for filename in os.listdir(base_path):
    if filename.endswith(".txt"):
        # Remove the .txt suffix to get the file's name
        name_without_suffix = filename[:-4]
        
        # Check if the name is a key in filtered_sync_data
        if name_without_suffix not in filtered_sync_data:
            # Move the file to the Filtered_out_of_JSON folder
            source_path = os.path.join(base_path, filename)
            destination_path = os.path.join(filtered_out_folder, filename)
            shutil.move(source_path, destination_path)

# Print results
prototype_pair_count = len(prototype_data)
filtered_sync_pair_count = len(filtered_sync_data)
print(f"Number of pairs in the prototype JSON: {prototype_pair_count}")
print(f"Number of pairs remaining in the synchronized JSON: {filtered_sync_pair_count}")
print(f"Files that did not match have been moved to: {filtered_out_folder}")

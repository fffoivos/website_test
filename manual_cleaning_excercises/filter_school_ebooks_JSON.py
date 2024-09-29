import os
import shutil
import json
import re

# Define paths
input_folder = "/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs"
output_folder = "/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs"
json_input_file = "/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/extracted_files.json"
json_output_file = "/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs/filtered_extracted_files.JSON"

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# Load the JSON data from the file
with open(json_input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Define the Greek words to filter out
greek_words = [
    "ΑΓΓΛΙΚΑ", "ΓΕΡΜΑΝΙΚΑ", "ΓΑΛΛΙΚΑ", "ΛΑΤΙΝΙΚΑ", 
    "ΔΑΣΚΑΛΟΥ", "ΚΑΘΗΓΗΤΗ", "ΛΥΣΕΙΣ", "ΑΣΚΗΣΕΩΝ", 
    "ΤΕΤΡΑΔΙΟ", "CD", "ΕΙΚΟΝΟΓΡΑΦΙΑ"
]

# Create a regex pattern that matches any of the Greek words
pattern = re.compile("|".join(greek_words))

# Filter the dictionary by checking if any Greek word is in the value
filtered_data = {k: v for k, v in data.items() if not pattern.search(v)}

# Calculate the difference in length
original_length = len(data)
filtered_length = len(filtered_data)
difference = original_length - filtered_length

print(f"Original length: {original_length}")
print(f"Filtered length: {filtered_length}")
print(f"Difference in length: {difference}")

# Read all the txt files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith(".txt"):
        # Extract the key name by removing the ".txt" extension
        key_name = file_name.rsplit(".", 1)[0]
        
        # Check if the file's name is in the filtered_data dictionary
        if key_name in filtered_data:
            # Copy the file to the output folder
            source_path = os.path.join(input_folder, file_name)
            destination_path = os.path.join(output_folder, file_name)
            shutil.copy2(source_path, destination_path)
            print(f"Copied: {file_name}")

# Save the filtered_data as a new JSON file
with open(json_output_file, "w", encoding="utf-8") as json_out:
    json.dump(filtered_data, json_out, ensure_ascii=False, indent=4)

print(f"Filtered JSON saved to {json_output_file}")

import os
import shutil
import json
import re

# Define paths
input_folder = "/home/fivos/Projects/GlossAPI/raw_txt/paste_texts"
json_input_file = os.path.join(input_folder, "pasted_texts.json")

# Define the path for the 'filtered_by_JSON' folder
filtered_folder = os.path.join(input_folder, "filtered_by_JSON")

# Ensure the 'filtered_by_JSON' folder exists
os.makedirs(filtered_folder, exist_ok=True)

# Load the JSON data from the file
with open(json_input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Define the Greek words to filter out
greek_words = [
    "ΑΓΓΛΙΚΑ", "ΓΕΡΜΑΝΙΚΑ", "ΓΑΛΛΙΚΑ", "ΛΑΤΙΝΙΚΑ", 
    "ΔΑΣΚΑΛΟΥ", "ΚΑΘΗΓΗΤΗ", "ΛΥΣΕΙΣ", "ΑΣΚΗΣΕΩΝ", 
    "ΤΕΤΡΑΔΙΟ", "CD", "ΕΙΚΟΝΟΓΡΑΦΙΑ", "Εσπερινού"
]

# Define the list of numbers
numbers = [
    106, 260, 440,
    182, 368, 458, 525, 626,
    237, 401, 402,
    301, 336, 724,
    255, 303,
    135, 381, 395, 459, 504, 513, 621, 704,
    221, 390,
    52, 111, 125, 444, 726,
    594,
    88,
    517,
    616,
    544,
    527,
    584,
    245
]

# Convert numbers list to a set of strings for efficient lookup
numbers_set = set(str(number) for number in numbers)

# Create a regex pattern that matches any of the Greek words
# Use re.IGNORECASE if you want case-insensitive matching
pattern = re.compile("|".join(greek_words), re.IGNORECASE)

# Function to extract number from key
def extract_number(key):
    match = re.search(r'paper_(\d+)', key)
    if match:
        return match.group(1)
    return None

# Filter the dictionary based on OR condition:
# Keep entries where the extracted number is in numbers_set OR the value contains any Greek word
filtered_data = {}
filtered_out_data = {}

for k, v in data.items():
    number = extract_number(k)
    if (number and number in numbers_set) or pattern.search(v):
        filtered_data[k] = v
    else:
        filtered_out_data[k] = v

# Calculate the difference in length
original_length = len(data)
filtered_length = len(filtered_data)
difference = original_length - filtered_length

print(f"Original number of entries: {original_length}")
print(f"Number of filtered entries: {filtered_length}")
print(f"Number of filtered-out entries: {difference}")

# Iterate over all .txt files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith(".txt"):
        # Extract the key name by removing the ".txt" extension
        key_name = file_name.rsplit(".", 1)[0]
        
        # If the key is NOT in filtered_data, move the file to 'filtered_by_JSON'
        if key_name not in filtered_data:
            source_path = os.path.join(input_folder, file_name)
            destination_path = os.path.join(filtered_folder, file_name)
            
            if os.path.exists(source_path):
                shutil.move(source_path, destination_path)
                print(f"Moved: {file_name} to 'filtered_by_JSON' folder")
            else:
                print(f"File not found and cannot be moved: {file_name}")

# Save the filtered_data back to the original JSON file
with open(json_input_file, "w", encoding="utf-8") as json_out:
    json.dump(filtered_data, json_out, ensure_ascii=False, indent=4)

print(f"Filtered JSON saved to {json_input_file}")

# Save the filtered_out_data as a new JSON file in 'filtered_by_JSON' folder
filtered_out_json_file = os.path.join(filtered_folder, "filtered_out_extracted_files.JSON")
with open(filtered_out_json_file, "w", encoding="utf-8") as json_out_filtered:
    json.dump(filtered_out_data, json_out_filtered, ensure_ascii=False, indent=4)

print(f"Filtered-out JSON saved to {filtered_out_json_file}")

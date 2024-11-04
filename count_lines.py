import json
import re

# Path to the JSON file
json_file_path = '/home/fivos/Projects/GlossAPI/downloaded_texts/pergamos/progress_report.json'

# Read the JSON file
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Initialize a list to store the numbers (n)
numbers = []

# Regex pattern to match keys of the form "paper_n"
pattern = re.compile(r'paper_(\d+)')

# Iterate over the keys in the dictionary
for key in data.keys():
    match = pattern.match(key)
    if match:
        # Extract the number n and convert to integer
        n = int(match.group(1))
        numbers.append(n)

# Find the maximum number n
max_n = max(numbers) if numbers else 0

# Count the total number of different n values
unique_numbers_count = len(set(numbers))

# Calculate the percentage of present numbers relative to max
percentage_present = (unique_numbers_count / max_n) * 100 if max_n > 0 else 0

# Print the results
print(f"Maximum number (n): {max_n}")
print(f"Count of unique numbers: {unique_numbers_count}")
print(f"Percentage of present numbers: {percentage_present:.2f}%")

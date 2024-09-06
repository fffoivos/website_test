import csv
import re

# Function to count alphanumeric characters in a string
def count_alphanumeric_characters(text):
    return len(re.findall(r'\w', text))  # \w matches any alphanumeric character (A-Z, a-z, 0-9, including _)

# Count alphanumeric characters in a .txt file
def count_alphanumeric_in_txt(txt_file):
    with open(txt_file, 'r', encoding='utf-8') as file:
        content = file.read()
        return count_alphanumeric_characters(content)

# Count alphanumeric characters in a CSV file under the "text" column
def count_alphanumeric_in_csv(csv_file):
    total_count = 0
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            text = row.get('text', '')  # Default to empty string if 'text' column is missing
            total_count += count_alphanumeric_characters(text)
    return total_count

# File paths (replace with actual paths)
txt_file = '/home/fivos/Downloads/dataset_dimotiki2.txt'
csv_file = '/home/fivos/Downloads/dataset_dimotiki2.csv'

# Count alphanumeric characters in both files
txt_count = count_alphanumeric_in_txt(txt_file)
csv_count = count_alphanumeric_in_csv(csv_file)

# Print the counts and comparison result
print(f"Alphanumeric characters in TXT file: {txt_count}")
print(f"Alphanumeric characters in CSV 'text' column: {csv_count}")

if txt_count == csv_count:
    print("The counts are equal.")
else:
    print("The counts are not equal.")

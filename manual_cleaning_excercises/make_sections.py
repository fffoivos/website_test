import os
import pandas as pd
import re

def is_uppercase_greek(text):
    # Split the text by spaces
    words = text.split()
    if not words:
        return []
    # Regular expression pattern to match Greek UPPERCASE letters and not lower case
    greek_uppercase_pattern = r'^((?!.*→α-ωά-ώ)[Α-ΩΆ-Ώ\d:\- ]+)$'
    # Collect all fully uppercase Greek words until a non-uppercase word is found
    uppercase_greek_words = []
    for word in words:
        if ( word.isupper() and re.match(greek_uppercase_pattern, word) ) or word in ["-", ":"] or word.isdigit():
            uppercase_greek_words.append(word)
        else:
            break
    
    for word in uppercase_greek_words:
        if word == "→":
            return []
        if len(word) > 1 and not word.isdigit():
            return uppercase_greek_words
    
    return []

def process_txt_files(input_folder):
    # Create the output folder as a subfolder of the input folder
    output_folder = os.path.join(input_folder, 'book_as_csv')
    os.makedirs(output_folder, exist_ok=True)

    # Compile the regex pattern
    greek_uppercase_pattern = r'^((?!.*→α-ωά-ώ)[Α-ΩΆ-Ώ\d:\- ]+)$'

    # Iterate over all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.csv")

            # Read the text file and process it
            with open(input_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Create a DataFrame
            df = pd.DataFrame({
                'index': range(1, len(lines) + 1),
                'text': [line.strip() for line in lines],
                'UP': [1 if is_uppercase_greek(line.strip()) else 0 for line in lines]
            })

            # Save the DataFrame as a CSV file
            df.to_csv(output_path, index=False)
            print(f"Processed {filename} and saved as {os.path.basename(output_path)}")

# Example usage
input_folder = '/home/fivos/Desktop/Projects/GlossAPI/raw_txt/sxolika/paste_texts'
process_txt_files(input_folder)
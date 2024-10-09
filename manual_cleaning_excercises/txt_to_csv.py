import os
import pandas as pd

def process_txt_files(input_folder):
    # Create the output folder as a subfolder of the input folder
    output_folder = os.path.join(input_folder, 'book_as_csv')
    os.makedirs(output_folder, exist_ok=True)

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
                'page': 0
            })

            # Save the DataFrame as a CSV file
            df.to_csv(output_path, index=False)
            print(f"Processed {filename} and saved as {os.path.basename(output_path)}")

# Example usage
input_folder = '/home/fivos/Desktop/Projects/GlossAPI/raw_txt/sxolika/paste_texts'
process_txt_files(input_folder)
import os
import json
import pandas as pd

def create_sxolika_dataset(txt_folder_path, json_file_path):
    """
    Creates a dataset by reading text files and a JSON dictionary,
    processing the data, and saving it as a CSV file.
    
    Parameters:
    - txt_folder_path: Path to the folder containing .txt files
    - json_file_path: Path to the JSON file containing the dictionary
    """
    
    # Initialize lists to store data
    texts = []
    sxolia = []
    taxis = []
    mathimata = []
    themata = []
    
    # Read the JSON dictionary
    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data_dict = json.load(json_file)
        print(f"Successfully loaded JSON data from {json_file_path}")
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    # Iterate through all .txt files in the specified folder
    try:
        for filename in os.listdir(txt_folder_path):
            if filename.endswith('.txt'):
                # Extract the key by removing the .txt extension
                key = os.path.splitext(filename)[0]
                
                txt_file_path = os.path.join(txt_folder_path, filename)
                
                # Read the content of the text file
                try:
                    with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
                        content = txt_file.read().strip()
                    print(f"Read content from {txt_file_path}")
                except Exception as e:
                    print(f"Error reading text file {txt_file_path}: {e}")
                    continue  # Skip to the next file
                
                # Get the corresponding value from the JSON dictionary
                if key in data_dict:
                    value = data_dict[key]
                    split_values = [item.strip() for item in value.split('>')]
                    
                    # Depending on the number of elements after splitting, assign values
                    if len(split_values) == 3:
                        sxolio = ""
                        taxi, mathima, thema = split_values
                    elif len(split_values) == 4:
                        sxolio, taxi, mathima, thema = split_values
                    else:
                        print(f"Unexpected number of elements after splitting for key '{key}': {split_values}")
                        sxolio, taxi, mathima, thema = "", "", "", ""
                    
                else:
                    print(f"Key '{key}' not found in JSON dictionary.")
                    sxolio, taxi, mathima, thema = "", "", "", ""
                
                # Append the data to the respective lists
                texts.append(content)
                sxolia.append(sxolio)
                taxis.append(taxi)
                mathimata.append(mathima)
                themata.append(thema)
    except Exception as e:
        print(f"Error processing text files: {e}")
        return
    
    # Create a DataFrame
    df = pd.DataFrame({
        'text': texts,
        'sxolio': sxolia,
        'taxi': taxis,
        'mathima': mathimata,
        'thema': themata
    })
    
    # Define the output CSV path
    output_csv_path = os.path.join(txt_folder_path, "sxolika_dataset.csv")
    
    # Save the DataFrame to a CSV file
    try:
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"Dataset successfully saved to {output_csv_path}")
    except Exception as e:
        print(f"Error saving CSV file: {e}")

# Example usage:
if __name__ == "__main__":
    # Replace these paths with your actual paths
    txt_folder = "/home/fivos/Desktop/text_sources/sxolika_vivlia/paste_texts/deduplicated_texts/unique/filtered_by_JSON/xondrikos_katharismos_papers/fine_cleaning_v4"
    json_file = "/home/fivos/Desktop/text_sources/sxolika_vivlia/paste_texts/deduplicated_texts/unique/filtered_by_JSON/xondrikos_katharismos_papers/fine_cleaning_v4/filtered_out_extracted_files.JSON"
    
    create_sxolika_dataset(txt_folder, json_file)

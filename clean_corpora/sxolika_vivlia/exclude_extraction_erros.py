import os
import shutil
import pandas as pd

def manage_papers(folder_path):
    """
    Manages paper files based on extraction errors.

    Parameters:
    - folder_path (str): The path to the main folder containing papers and the statistics folder.
    """

    # Define paths
    statistics_path = os.path.join(folder_path, 'statistics', 'extreme_values.csv')
    excluded_papers_path = os.path.join(folder_path, 'excluded_papers')

    # Check if the CSV file exists
    if not os.path.isfile(statistics_path):
        print(f"Error: The file {statistics_path} does not exist.")
        return

    # Create 'excluded_papers' directory if it doesn't exist
    os.makedirs(excluded_papers_path, exist_ok=True)
    print(f"Ensured that the directory '{excluded_papers_path}' exists.")

    try:
        # Read the CSV file
        df = pd.read_csv(statistics_path)
        print(f"Successfully read the CSV file: {statistics_path}")
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        file_name = row['filename']
        extract_error = row['extraction_error']

        source_file_path = os.path.join(folder_path, file_name)
        excluded_file_path = os.path.join(excluded_papers_path, file_name)

        if extract_error == 1:
            # Move the file to 'excluded_papers' if it exists in the main folder
            if os.path.isfile(source_file_path):
                try:
                    shutil.move(source_file_path, excluded_file_path)
                    print(f"Moved '{file_name}' to 'excluded_papers'.")
                except Exception as e:
                    print(f"Error for moving '{file_name}' to 'excluded_papers': {e}")
            else:
                #sparse message
                print(" ")
        elif extract_error == 0:
            # Move the file back to the main folder if it exists in 'excluded_papers'
            if os.path.isfile(excluded_file_path):
                try:
                    shutil.move(excluded_file_path, source_file_path)
                    print(f"Moved '{file_name}' back to '{folder_path}'.")
                except Exception as e:
                    print(f"Error for moving '{file_name}' back to '{folder_path}': {e}")
            else:
                #sparse message
                print(" ")

if __name__ == "__main__":
    folder_path = '/home/fivos/Desktop/text_sources/sxolika_vivlia/paste_texts/deduplicated_texts/unique/filtered_by_JSON/xondrikos_katharismos_papers/fine_cleaning_v4'
    manage_papers(folder_path)

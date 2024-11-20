import os
import pandas as pd
import re

def process_lesson_files(folder_path):
    """
    Process lesson text files and create both CSV and Parquet files with lesson titles and content.
    
    Args:
        folder_path (str): Path to the folder containing lesson files and metadata
    """
    # Read the metadata file
    metadata_path = os.path.join(folder_path, 'lesson_metadata.csv')
    metadata_df = pd.read_csv(metadata_path)
    
    # Initialize lists to store data for the new files
    titles = []
    contents = []
    
    # Get all txt files in the directory
    txt_files = [f for f in os.listdir(folder_path) if f.startswith('lesson_') and f.endswith('.txt')]
    
    for file_name in txt_files:
        # Extract lesson number using regex
        match = re.search(r'lesson_(\d+)', file_name)
        if match:
            lesson_number = int(match.group(1))
            
            # Look up the lesson title from metadata
            lesson_row = metadata_df[metadata_df['Lesson Number'] == lesson_number]
            if not lesson_row.empty:
                lesson_title = lesson_row['Lesson Title'].iloc[0]
                
                # Read the content of the text file
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Add to our lists
                titles.append(lesson_title)
                contents.append(content)
    
    # Create the DataFrame
    result_df = pd.DataFrame({
        'title': titles,
        'text': contents
    })
    
    # Save to CSV
    csv_output_path = os.path.join(folder_path, 'dimodous_mathimata.csv')
    result_df.to_csv(csv_output_path, index=False)
    
    # Save to Parquet
    parquet_output_path = os.path.join(folder_path, 'dimodous_mathimata.parquet')
    result_df.to_parquet(parquet_output_path, index=False)
    
    print(f"Processed {len(titles)} lesson files.")
    print(f"CSV output saved to: {csv_output_path}")
    print(f"Parquet output saved to: {parquet_output_path}")

# Example usage:
if __name__ == "__main__":
    # Replace with your folder path
    folder_path = "/home/fivos/Desktop/text_sources/dimodis/dimodis_lesson_texts/processed_files"
    process_lesson_files(folder_path)

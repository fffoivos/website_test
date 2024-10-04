import os

# Function to compute average word count for each file
def calculate_word_count(file_path, c=0.0, avg_chars_per_word=5, avg_chars_per_line=60):
    """
    Calculate the estimated word count of a file.
    
    :param file_path: The path to the file.
    :param c: Cleaning factor, a percentage (0 <= c < 1) to reduce the line count.
    :param avg_chars_per_word: Average number of characters per word.
    :param avg_chars_per_line: Average number of characters per line.
    :return: Estimated word count after applying the cleaning factor.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Calculate total lines in file
    total_lines = len(lines)
    
    # Estimate average words per line
    avg_words_per_line = avg_chars_per_line / avg_chars_per_word
    
    # Adjust for the cleaning factor
    cleaned_lines = total_lines * (1 - c)
    
    # Estimated total word count for this file
    estimated_word_count = avg_words_per_line * cleaned_lines
    
    return estimated_word_count

# Function to process all .txt files in a given folder
def process_folder(folder_path, cleaning_factor=0.0, avg_chars_per_word=5, avg_chars_per_line=60):
    """
    Process all text files in the folder and calculate the total estimated word count.
    
    :param folder_path: The folder path containing .txt files.
    :param cleaning_factor: Cleaning factor to reduce the number of lines.
    :param avg_chars_per_word: Average number of characters per word.
    :param avg_chars_per_line: Average number of characters per line.
    :return: Total estimated word count for the folder.
    """
    total_word_count = 0
    file_count = 0
    
    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            file_count += 1
            
            # Calculate word count for the file
            word_count = calculate_word_count(file_path, cleaning_factor, avg_chars_per_word, avg_chars_per_line)
            total_word_count += word_count
    
    # Save the total word count to a text file
    result_file_path = os.path.join(folder_path, 'word_count.txt')
    with open(result_file_path, 'w', encoding='utf-8') as result_file:
        result_file.write(f"Total Word Count: {total_word_count}\n")
        result_file.write(f"Number of Files Processed: {file_count}\n")
    
    print(f"Processed {file_count} .txt files. Total estimated word count: {total_word_count}")
    print(f"Result saved in {result_file_path}")

# Example usage
folder_path = '/home/fivos/Desktop/New Folder/Sxolika/filtered_by_JSON/cleaned_filtered_extracted_txt/'  # Replace with the actual folder path
cleaning_factor = 0.0  # Adjust the cleaning factor as needed (0.0 means no reduction)
process_folder(folder_path, cleaning_factor)

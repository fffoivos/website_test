import os
import re
import unicodedata
import math
import matplotlib.pyplot as plt

# Define the directory paths
input_directory = '/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs'
output_directory = os.path.join(input_directory, 'cleaned_filtered_extracted_pdfs')

# Create the output and statistics directories if they don't exist
os.makedirs(output_directory, exist_ok=True)
statistics_directory = os.path.join(output_directory, 'statistics')
os.makedirs(statistics_directory, exist_ok=True)

# Regex patterns
index_pattern = re.compile(r"([α-ωΑ-Ωά-ώ\d:]+)\s{0,4}(?:[.ο•]{4,}|(?:[.ο•]+\s{1,2})+[.ο•]+)(\s{0,2}σελ\.)?\s{0,4}\d+(?!\S)")
bibliography_pattern = re.compile(r".*βιβλιογραφια.*", re.IGNORECASE)
legal_statement_pattern = re.compile(r".*Βάσει του ν\. 3966/2011 τα διδακτικά βιβλία.*", re.IGNORECASE)
page_seven_adobe_format = re.compile(r".+\.(indd|indb)\s{0,3}[7]")
page_seven_other_format = re.compile(r"\d{1,2}\/\d{1,2}\/\d{2}\s+\d{1,2}:\d{2}\s+(?:AM|PM)\s+Page\s+7")

# Functions
def find_bibliography_line(line):
    accentless_line = ''.join(c for c in unicodedata.normalize('NFD', line) if unicodedata.category(c) != 'Mn')
    concat_line = re.sub(r'[^α-ωΑ-Ω]', '', accentless_line)
    return bibliography_pattern.match(concat_line.lower()) if len(concat_line) < 40 else False

def find_legal_statement_line(line):
    return legal_statement_pattern.match(line.lower())

def process_file(file_path):
    last_index_line_number = 0
    bibliography_line_number = None
    legal_statement_line_number = None
    seventh_page_line_number = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        txt_length = len(lines)
        bibliography_line_number = txt_length
        
        for line_number, line in enumerate(lines, 1):
            if (line_number / txt_length) < 0.5 and index_pattern.search(line):
                last_index_line_number = line_number
            
            if (line_number / txt_length) > 0.9 and find_bibliography_line(line):
                bibliography_line_number = line_number - 1
                break
            
            if bibliography_line_number == txt_length and find_legal_statement_line(line):
                bibliography_line_number = line_number - 1
        
        if last_index_line_number == 0 and seventh_page_line_number:
            last_index_line_number = seventh_page_line_number

    return last_index_line_number, bibliography_line_number, lines

def calculate_statistics(file_distances):
    total_lines_removed = 0
    total_lines = 0
    total_characters = 0
    total_lines_in_all_files = 0
    removal_rates = []
    line_totals = []
    avg_chars_per_file = []
    
    for filename, distance, txt_length, lines in file_distances:
        removal_rate = (distance / txt_length) * 100
        removal_rates.append(removal_rate)
        total_lines_removed += distance
        total_lines += txt_length
        line_totals.append(txt_length)

        # Calculate the average characters per line for this file
        total_characters_in_file = sum(len(line) for line in lines)
        total_characters += total_characters_in_file
        avg_chars_per_line_in_file = total_characters_in_file / txt_length
        avg_chars_per_file.append(avg_chars_per_line_in_file)

        # Track total number of lines for global average calculation
        total_lines_in_all_files += txt_length

    average_removal_rate = (total_lines_removed / total_lines) * 100
    average_lines = total_lines / len(file_distances)
    
    # Calculate the global average characters per line
    average_chars_per_line = total_characters / total_lines_in_all_files
    
    return removal_rates, average_removal_rate, line_totals, average_lines, total_lines, avg_chars_per_file, average_chars_per_line

def save_statistics(file_distances, removal_rates, average_removal_rate, line_totals, average_lines, total_lines, avg_chars_per_file, average_chars_per_line):
    stats_file_path = os.path.join(statistics_directory, 'removal_statistics.txt')
    
    with open(stats_file_path, 'w') as stats_file:
        stats_file.write(f"Average Removal Rate: {average_removal_rate:.2f}%\n")
        stats_file.write(f"Average Total Lines: {average_lines:.2f}\n")
        stats_file.write(f"Total Lines Across All Files: {total_lines}\n")
        stats_file.write(f"Average Characters per Line Across All Files: {average_chars_per_line:.2f}\n\n")
        
        stats_file.write("File Statistics (Lines Removed, Total Lines, Avg Characters per Line):\n")
        for i, (filename, _, _, _) in enumerate(file_distances):
            stats_file.write(f"{filename}: {removal_rates[i]:.2f}% removed, {line_totals[i]} total lines, {avg_chars_per_file[i]:.2f} avg chars/line\n")
    
    # Plotting the distribution of removal rates
    plt.hist(removal_rates, bins=10, color='blue', edgecolor='black')
    plt.title('Distribution of Line Removal Rates')
    plt.xlabel('Removal Rate (%)')
    plt.ylabel('Number of Files')
    
    plt_file_path = os.path.join(statistics_directory, 'removal_rate_distribution.png')
    plt.savefig(plt_file_path)
    plt.close()

    # Plotting the distribution of total lines
    plt.hist(line_totals, bins=10, color='green', edgecolor='black')
    plt.title('Distribution of Total Lines')
    plt.xlabel('Total Lines')
    plt.ylabel('Number of Files')

    plt_file_path = os.path.join(statistics_directory, 'total_lines_distribution.png')
    plt.savefig(plt_file_path)
    plt.close()

    # Plotting the distribution of average characters per line
    plt.hist(avg_chars_per_file, bins=10, color='purple', edgecolor='black')
    plt.title('Distribution of Average Characters per Line')
    plt.xlabel('Average Characters per Line')
    plt.ylabel('Number of Files')

    plt_file_path = os.path.join(statistics_directory, 'avg_chars_per_line_distribution.png')
    plt.savefig(plt_file_path)
    plt.close()

def main():
    file_distances = []

    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        
        if os.path.isdir(file_path) or not filename.endswith('.txt'):
            continue
        
        print(f"Processing {filename}")
        last_index_line_number, bibliography_line_number, lines = process_file(file_path)
        
        txt_length = len(lines)
        distance = txt_length - bibliography_line_number
        file_distances.append((filename, distance, txt_length, lines))  # Pass the actual lines for character calculations
        
        output_lines = []
        inside_content = False
        for line_number, line in enumerate(lines, 1):
            if line_number == last_index_line_number + 1:
                inside_content = True
            if line_number == bibliography_line_number + 1:
                inside_content = False
            if inside_content:
                output_lines.append(line)
        
        output_file_path = os.path.join(output_directory, filename)
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.writelines(output_lines)
    
    removal_rates, average_removal_rate, line_totals, average_lines, total_lines, avg_chars_per_file, average_chars_per_line = calculate_statistics(file_distances)
    save_statistics(file_distances, removal_rates, average_removal_rate, line_totals, average_lines, total_lines, avg_chars_per_file, average_chars_per_line)

if __name__ == '__main__':
    main()

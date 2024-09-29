import pandas as pd
import re

# File paths
errors_file = '/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs/cleaned_filtered_extracted_pdfs/statistics/extraction_errors.csv'
statistics_file = '/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs/cleaned_filtered_extracted_pdfs/statistics/removal_statistics.txt'

# Read the extraction errors CSV
errors_df = pd.read_csv(errors_file)

# Prepare regex pattern to match each line in the statistics file
pattern = r"(?P<filename>\w+\.txt):\s(?P<percent_removed>\d+\.\d+)% removed,\s(?P<total_lines>\d+) total lines,\s(?P<avg_chars_per_line>\d+\.\d+) avg chars/line"

# Initialize list to hold the parsed data
data = []

# Read and parse the statistics file
with open(statistics_file, 'r') as file:
    lines = file.readlines()

# Iterate through each line to match the pattern
for line in lines:
    match = re.match(pattern, line)
    if match:
        # Extract data from the regex match
        file_name = match.group('filename')
        percent_removed = float(match.group('percent_removed'))
        total_lines = int(match.group('total_lines'))
        avg_chars_per_line = float(match.group('avg_chars_per_line'))

        # Check if the file exists in extraction_errors.csv and if extract_error == 1
        error_row = errors_df[errors_df['file_name'] == file_name]
        if error_row.empty or error_row['extract_error'].iloc[0] != 1:
            # Add to the data list
            data.append({
                'file_name': file_name,
                'percent_removed': percent_removed,
                'total_lines': total_lines,
                'avg_chars_per_line': avg_chars_per_line
            })

# Create a DataFrame from the parsed data
mean_values_df = pd.DataFrame(data)

# Save the DataFrame to a CSV file
output_path = '/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs/cleaned_filtered_extracted_pdfs/statistics/mean_values.csv'
mean_values_df.to_csv(output_path, index=False)

print(f"mean_values.csv has been saved to {output_path}")

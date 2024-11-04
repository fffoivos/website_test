import os
import re
import csv

# Define the page marker regex
page_marker_regex = re.compile(r'^((\d){1,2}|(. (\d) .)|\[(\d)\]|[ivxc]{1,6})')

# Function to process a single text file and save to CSV
def process_file(file_path, output_dir):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split text by the page marker regex and capture page numbers
    matches = list(page_marker_regex.finditer(content))
    
    if not matches:
        print(f"No page markers found in {file_path}")
        return

    # Create output folder if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Prepare data for the CSV
    rows = []

    # Iterate over the matches and split pages
    for i, match in enumerate(matches):
        page_number = match.group(1)  # Extract the page number
        start_index = match.end()  # Get the end of the current match

        # Determine the end of the current page (start of the next match or end of the file)
        if i + 1 < len(matches):
            end_index = matches[i + 1].start()
        else:
            end_index = len(content)

        # Extract page content and strip whitespace
        page_content = content[start_index:end_index].strip()

        # Add row with page content and page number to the list, exclude empty content
        if page_content:  # Avoid saving empty content
            rows.append([page_content, page_number])

    # Generate the output CSV file path
    file_name = os.path.splitext(os.path.basename(file_path))[0]  # Get filename without extension
    output_csv = os.path.join(output_dir, f'{file_name}.csv')

    # Write data to CSV with columns 'text' and 'page'
    with open(output_csv, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['text', 'page'])  # Write header
        writer.writerows(rows)  # Write page content and numbers

    print(f"Processed and saved {output_csv}")

# Main function to process all txt files in the input directory
def process_directory(input_dir):
    output_dir = os.path.join(input_dir, 'extracted_pages')
    os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist

    for file_name in os.listdir(input_dir):
        if file_name.endswith('.txt'):
            file_path = os.path.join(input_dir, file_name)
            process_file(file_path, output_dir)

# Example usage
input_folder = '/home/fivos/Desktop/Projects/GlossAPI/raw_txt/sxolika/paste_texts'
process_directory(input_folder)

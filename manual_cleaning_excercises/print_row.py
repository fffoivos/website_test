import csv

def read_csv_row_with_headers(file_path, row_index):
    try:
        with open(file_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            headers = next(csv_reader)  # Read the header row
            for i, row in enumerate(csv_reader):
                if i == row_index - 1:  # Subtract 1 because we already read the header
                    return headers, row
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
    return None, None

file_path = '/home/fivos/Desktop/cleaned_filtered_extracted_txt/fine_cleaning/extracted_pages/test/paper_28_sections.csv'
row_index = 374

headers, row = read_csv_row_with_headers(file_path, row_index)

if headers and row:
    print(f"Row {row_index}:")
    for header, value in zip(headers, row):
        print(f"{header}: {value}")
else:
    print(f"Row {row_index} not found or error occurred.")
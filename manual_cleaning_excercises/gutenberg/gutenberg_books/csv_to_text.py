import csv
import os
import sys

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

def process_csv(csv_path):
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            print("Column names found in the CSV:")
            print(reader.fieldnames)
            
            success_count = 0
            error_count = 0
            
            for row_number, row in enumerate(reader, start=1):
                try:
                    text = row['text']
                    author = row['author']
                    title = row['title']
                    
                    # Create filename
                    title_words = title.split()
                    title_part = "_".join(title_words)[:5]
                    while len(title_part) < 5 and title_words:
                        title_part += "_" + title_words[len(title_part.split("_"))]
                    
                    filename = f"{author}_{title_part}.txt"
                    
                    # Ensure filename is valid
                    filename = "".join(c for c in filename if c.isalnum() or c in ['_', '.'])
                    
                    # Write to file
                    with open(filename, 'w', encoding='utf-8') as txtfile:
                        txtfile.write(text)
                    
                    print(f"Created file: {filename}")
                    success_count += 1
                    
                except KeyError as e:
                    print(f"Error processing row {row_number}: Missing key {e}")
                    error_count += 1
                except Exception as e:
                    print(f"Error processing row {row_number}: {e}")
                    error_count += 1
            
            print(f"\nProcessing complete. Successfully processed {success_count} books.")
            print(f"Encountered errors in {error_count} rows.")
                    
    except Exception as e:
        print(f"Error opening or reading the file: {e}")

# Usage
csv_path = '/home/fivos/Downloads/gutenberg_greek_books.csv'
process_csv(csv_path)

import os
import shutil
from pathlib import Path

# Define paths
output_dir = "/home/fivos/Desktop/extraction_tests/ypologistis_mou_output"
source_dir = "/home/fivos/Desktop/extraction_tests/ypologistis_moy"
processed_dir = "/home/fivos/Desktop/extraction_tests/processed_from_ypologistis_moy"

# Create processed directory if it doesn't exist
os.makedirs(processed_dir, exist_ok=True)

# Get list of successfully converted files (md files)
md_files = [f for f in os.listdir(output_dir) if f.endswith('.md')]

# Move corresponding PDF files
moved_count = 0
for md_file in md_files:
    # Get the base name without extension
    base_name = os.path.splitext(md_file)[0]
    pdf_file = f"{base_name}.pdf"
    source_path = os.path.join(source_dir, pdf_file)
    dest_path = os.path.join(processed_dir, pdf_file)
    
    if os.path.exists(source_path):
        shutil.move(source_path, dest_path)
        moved_count += 1
        print(f"Moved: {pdf_file}")

print(f"\nTotal files moved: {moved_count}")

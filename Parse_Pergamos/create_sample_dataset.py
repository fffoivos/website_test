#!/usr/bin/env python3
import os
import random
from new_academin_paper_formatting import format_academic_document_with_positions
import csv

def main():
    # Set paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, 'extraction_separation_combined/well_extracted')
    output_dir = os.path.join(base_dir, 'sample_output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all markdown files
    all_papers = [f for f in os.listdir(input_dir) if f.endswith('.md')]
    print(f"Found {len(all_papers)} papers in total")
    
    # Randomly select 300 papers
    sample_size = 300
    selected_papers = random.sample(all_papers, sample_size)
    print(f"Randomly selected {sample_size} papers")
    
    # Save the list of selected papers for reference
    selected_papers_file = os.path.join(output_dir, "selected_papers.txt")
    with open(selected_papers_file, 'w', encoding='utf-8') as f:
        for paper in selected_papers:
            f.write(f"{paper}\n")
    print(f"Saved list of selected papers to {selected_papers_file}")
    
    # Process the selected papers
    csv_path = os.path.join(output_dir, "sections_for_annotation.csv")
    all_rows = []
    
    for filename in selected_papers:
        input_path = os.path.join(input_dir, filename)
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Get row data
            short_name = os.path.splitext(filename)[0]
            doc_rows = format_academic_document_with_positions(text, short_name)
            all_rows.extend(doc_rows)
            print(f"Processed {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    # Write them out as CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ["filename", "header", "place", "section", "label"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)
    
    print(f"Saved {len(all_rows)} rows to {csv_path}")

if __name__ == "__main__":
    main()

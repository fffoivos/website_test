import pandas as pd

def split_csv_for_annotation(input_file, output_dir, rows_per_file=1000):
    """Split a CSV file into multiple files with specified number of rows."""
    # Read the input CSV
    df = pd.read_csv(input_file)
    
    # Calculate how many complete files we can make
    total_rows = len(df)
    num_files = min(4, (total_rows + rows_per_file - 1) // rows_per_file)
    
    print(f"Splitting {total_rows} rows into {num_files} files...")
    
    # Split and save files
    for i in range(num_files):
        start_idx = i * rows_per_file
        end_idx = min(start_idx + rows_per_file, total_rows)
        
        # Extract subset
        subset_df = df.iloc[start_idx:end_idx].copy()
        
        # Create output filename
        output_file = f"{output_dir}/list_rows_sections_for_annotation_part{i+1}.csv"
        
        # Save to CSV
        subset_df.to_csv(output_file, index=False)
        print(f"Part {i+1}: Saved rows {start_idx+1}-{end_idx} to {output_file}")

if __name__ == "__main__":
    input_file = "/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/list_rows_sections_for_annotation.csv"
    output_dir = "/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output"
    
    split_csv_for_annotation(input_file, output_dir)

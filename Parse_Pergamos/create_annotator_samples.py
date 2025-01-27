import pandas as pd

# Read the CSV file
csv_path = '/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/sections_for_annotation.csv'
df = pd.read_csv(csv_path)

# Get rows with has_table=True
table_rows = df[df['has_table'] == True].copy()

# Create a dictionary to store previous headers
prev_headers = {}

# For each table row, find the previous row's header
for idx in table_rows.index:
    if idx > 0:  # Make sure we're not at the first row
        # Get the previous row's header
        prev_header = df.loc[idx - 1, 'header']
        prev_headers[idx] = prev_header
    else:
        prev_headers[idx] = ''  # Empty string for first row

# Add the previous headers as a new column
table_rows['prev_header'] = table_rows.index.map(prev_headers)

# Function to check if section is a proper table
def is_proper_table(section):
    if not isinstance(section, str):
        return False
    
    lines = section.strip().split('\n')
    
    # Count sequences of 4 or more dots
    dot_sequences = 0
    for line in lines:
        if '....' in line:
            dot_sequences += 1
    
    # Check if there are at least 2 lines with sequences of dots
    if dot_sequences < 2:
        return False
    
    # Count lines that don't start with '|'
    non_pipe_lines = 0
    for line in lines:
        if line.strip() and not line.strip().startswith('|'):
            non_pipe_lines += 1
            
    # Allow up to 3 lines that don't start with '|'
    if non_pipe_lines > 3:
        return False
    
    return True

# Add label column
table_rows['label'] = table_rows['section'].apply(lambda x: 'π' if is_proper_table(x) else '')

# Reorder columns to put prev_header before header
cols = table_rows.columns.tolist()
header_idx = cols.index('header')
prev_header_idx = cols.index('prev_header')
cols.pop(prev_header_idx)
cols.insert(header_idx, 'prev_header')
table_rows = table_rows[cols]

# Split the dataframe into two equal parts
half_size = len(table_rows) // 2
katerina_df = table_rows.iloc[:half_size]
ioanna_df = table_rows.iloc[half_size:]

# Save to CSV files
output_dir = '/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output'
katerina_df.to_csv(f'{output_dir}/Katerina_sample_dataset.csv', index=False)
ioanna_df.to_csv(f'{output_dir}/Ioanna_sample_dataset.csv', index=False)

print(f"Total rows with tables: {len(table_rows)}")
print(f"Rows in Katerina's dataset: {len(katerina_df)}")
print(f"Rows in Ioanna's dataset: {len(ioanna_df)}")
print(f"Number of proper tables (π): {table_rows['label'].value_counts().get('π', 0)}")

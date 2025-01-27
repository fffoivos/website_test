import pandas as pd

# Read Katerina's dataset
csv_path = '/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/Katerina_sample_dataset.csv'
df = pd.read_csv(csv_path)

# Get the first row's section content
first_row_section = df.iloc[0]['section']

print("First row section content:")
print("-" * 50)
print(first_row_section)
print("-" * 50)
print(f"Number of '....' occurrences: {first_row_section.count('....)') if isinstance(first_row_section, str) else 0}")
print("\nChecking each line:")
if isinstance(first_row_section, str):
    for i, line in enumerate(first_row_section.split('\n')):
        if line.strip():
            print(f"Line {i+1} starts with '|': {line.strip().startswith('|')} | Content: {line.strip()}")

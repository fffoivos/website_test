import pandas as pd

# Read the CSV file
csv_path = '/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/sections_for_annotation.csv'
df = pd.read_csv(csv_path)

# Count rows where has_table is True
tables_count = df['has_table'].sum()

# Count rows where either has_table or has_list is True
tables_or_lists_count = df['has_table'].astype(bool) | df['has_list'].astype(bool)
total_with_either = tables_or_lists_count.sum()

print(f"Number of sections with tables: {tables_count}")
print(f"Number of sections with either tables or lists: {total_with_either}")
print(f"Total number of sections: {len(df)}")
print(f"Percentage with tables: {(tables_count/len(df))*100:.2f}%")
print(f"Percentage with tables or lists: {(total_with_either/len(df))*100:.2f}%")

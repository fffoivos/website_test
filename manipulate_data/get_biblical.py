import pandas as pd

# Read the file
file_path = '/home/fivos/Documents/bible_kathara.txt'  # Replace with your actual file path
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Prepare the data
data = []
for line in lines:
    # Remove leading numbers and whitespace
    cleaned_text = ' '.join(line.split()[1:])
    data.append({'text': cleaned_text, 'Ποικιλία': 3, 'archaia_or_not': 1})

# Create DataFrame
df = pd.DataFrame(data)

# Save DataFrame to CSV
output_file_path = '/home/fivos/Documents/biblical_kathar.csv'  # Replace with your desired output file path
df.to_csv(output_file_path, index=False, encoding='utf-8')

print(f"DataFrame saved as {output_file_path}")

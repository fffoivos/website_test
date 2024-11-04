import os
import pandas as pd
import random
import string

# Define the paths
outpages_path = '/home/fivos/Desktop/Page_extraction/OUTPAGES/'
inpages_path = '/home/fivos/Desktop/Page_extraction/INPAGES/'
stopwords_path = '/home/fivos/Downloads/stopwords-el.txt'
output_csv_path = '/home/fivos/Desktop/Page_extraction/cleaned_pages.csv'  # Path to save the final CSV

# Helper function to clean text
def clean_text(text, stopwords):
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Tokenize and remove stopwords
    tokens = text.split()
    cleaned_tokens = [word for word in tokens if word.lower() not in stopwords]
    return ' '.join(cleaned_tokens)

# Load stopwords
with open(stopwords_path, 'r', encoding='utf-8') as f:
    stopwords = set(f.read().splitlines())

# Read OUTPAGES
out_files = os.listdir(outpages_path)
out_texts = []
for file in out_files:
    with open(os.path.join(outpages_path, file), 'r', encoding='utf-8') as f:
        out_texts.append(f.read())

# Create DataFrame with OUT entries
data = pd.DataFrame({'text': out_texts, 'place': 'OUT'})

# Read INPAGES and sample equal number of files
in_files = os.listdir(inpages_path)
sampled_in_files = random.sample(in_files, len(out_files))
in_texts = []
for file in sampled_in_files:
    with open(os.path.join(inpages_path, file), 'r', encoding='utf-8') as f:
        in_texts.append(f.read())

# Add IN entries to the DataFrame
in_data = pd.DataFrame({'text': in_texts, 'place': 'IN'})
data = pd.concat([data, in_data], ignore_index=True)

# Clean the text in the DataFrame
data['text'] = data['text'].apply(lambda x: clean_text(x, stopwords))

# Save the cleaned DataFrame to a CSV file
data.to_csv(output_csv_path, index=False)

print(f"Data has been saved to {output_csv_path}")

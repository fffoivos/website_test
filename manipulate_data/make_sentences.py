import csv
import re

# Define the path to the input file and output CSV file
input_file = "/home/fivos/Downloads/dataset_dimotiki2.txt"
output_file = "/home/fivos/Downloads/dataset_dimotiki2.csv"

# Regex pattern to match Greek sentence ending punctuation marks: ".", "!", ";"
sentence_endings = r'[.!;]'

# Initialize a variable to store the total number of alphanumeric characters from rejected sentences
total_rejected_characters = 0

# Function to count alphanumeric characters in a string
def count_alphanumeric_characters(text):
    # Use regex to find all alphanumeric characters (letters and digits)
    return len(re.findall(r'\w', text))

# Modify the split_sentences function to include rejected sentences processing
def split_sentences(text):
    global total_rejected_characters
    # Split the text into sentences using the punctuation marks defined
    sentences = re.split(sentence_endings, text)
    
    # Initialize list for valid sentences and process sentences
    valid_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        # Check if the sentence is non-empty and has more than 4 words
        if sentence and len(sentence.split()) > 4:
            valid_sentences.append(sentence)
        else:
            # If the sentence is rejected, count its alphanumeric characters
            total_rejected_characters += count_alphanumeric_characters(sentence)
    
    return valid_sentences

# Function to process paragraphs
def process_paragraphs(paragraphs):
    grouped_sentences = []
    for paragraph in paragraphs:
        sentences = split_sentences(paragraph)
        for i in range(0, len(sentences), 2):
            # Join sentences in pairs, even if there's one sentence left at the end
            sentence_group = " ".join(sentences[i:i+2])
            if sentence_group.strip():  # Ensure the group is not empty
                grouped_sentences.append(sentence_group)
    return grouped_sentences

# Read the input file and process line by line
with open(input_file, 'r', encoding='utf-8') as file, \
     open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['text'])  # Write the header
    
    current_paragraph = []
    for line in file:
        if line.strip():  # Process non-empty lines
            current_paragraph.append(line.strip())
        else:
            # Process the current paragraph when an empty line is encountered
            if current_paragraph:
                paragraph_text = ' '.join(current_paragraph)  # Join lines into one paragraph
                grouped_sentences = process_paragraphs([paragraph_text])
                for group in grouped_sentences:
                    csvwriter.writerow([group])
                current_paragraph = []  # Reset paragraph buffer
    
    # Process any remaining paragraph at the end of the file
    if current_paragraph:
        paragraph_text = ' '.join(current_paragraph)
        grouped_sentences = process_paragraphs([paragraph_text])
        for group in grouped_sentences:
            csvwriter.writerow([group])

# Print the total alphanumeric characters in rejected sentences
print(f"Total alphanumeric characters in rejected sentences: {total_rejected_characters}")
print(f"Parsed data has been written to {output_file}")

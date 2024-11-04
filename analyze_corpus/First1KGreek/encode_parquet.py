import pandas as pd
import re

# Load the DataFrame
df = pd.read_parquet('/home/fivos/Desktop/text_sources/greek_pd_1.parquet')

# Character mapping dictionary
char_mapping = {
    # Latin to Greek uppercase
    'A': 'Α', 'B': 'Β', 'E': 'Ε', 'Z': 'Ζ', 'H': 'Η', 'I': 'Ι',
    'K': 'Κ', 'M': 'Μ', 'N': 'Ν', 'O': 'Ο', 'P': 'Ρ', 'T': 'Τ',
    'Y': 'Υ', 'X': 'Χ', 'S': 'Σ', 'D': 'Δ', 'F': 'Φ', 'W': 'Ω',
    'C': 'Σ', 'V': 'Ν', 'J': 'Ι', 'Q': 'Θ', 'G': 'Γ',
    # Latin to Greek lowercase
    'a': 'α', 'b': 'β', 'e': 'ε', 'z': 'ζ', 'h': 'η', 'i': 'ι',
    'k': 'κ', 'm': 'μ', 'n': 'ν', 'o': 'ο', 'p': 'ρ', 't': 'τ',
    'y': 'υ', 'x': 'χ', 's': 'σ', 'd': 'δ', 'f': 'φ', 'w': 'ω',
    'c': 'ς', 'v': 'ν', 'j': 'ι', 'q': 'θ', 'g': 'γ',
    # Common misread symbols
    '{': '', '}': '', '[': '', ']': '', '^': '', '<': '', '>': '',
    '`': "'", '\"': '"', '”': '"', '“': '"', '‘': "'", '’': "'",
    '|': '', '\\': '', '/': '', '_': '', '=': '', '+': '',
    # Fix common OCR errors
    'II': 'Π', 'll': 'π', '11': 'Π', '0': 'Ο', '5': 'Σ', '§': 'ς',
}

def clean_text(text):
    # Remove phrases like "Digitized by Google"
    text = re.sub(r'.*Digitized by Google.*\n?', '', text, flags=re.IGNORECASE)
    # Remove extraneous symbols
    text = re.sub(r'[^\w\sΑ-Ωα-ωάέήίόύώϊϋΐΰς΄ΐΰῗῥ]', '', text)
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def correct_characters(text):
    for wrong_char, correct_char in char_mapping.items():
        text = text.replace(wrong_char, correct_char)
    return text

# Optional: Install a Greek spell checker if available
# from symspellpy import SymSpell, Verbosity

# def correct_spelling(text):
#     # Initialize SymSpell object and load Greek dictionary
#     sym_spell = SymSpell(max_dictionary_edit_distance=2)
#     sym_spell.load_dictionary('greek_dictionary.txt', term_index=0, count_index=1)
#     corrected_text = []
#     for word in text.split():
#         suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
#         if suggestions:
#             corrected_word = suggestions[0].term
#         else:
#             corrected_word = word
#         corrected_text.append(corrected_word)
#     return ' '.join(corrected_text)

def process_text(text):
    text = clean_text(text)
    text = correct_characters(text)
    # Uncomment the following line if using spell checker
    # text = correct_spelling(text)
    return text

# Apply to each entry and print the corrected text
for index, row in df.head(10).iterrows():
    original_text = row['text']
    corrected_text = process_text(original_text)
    print(f"--- Corrected Entry {index + 1} ---")
    print(corrected_text)
    print('\n')

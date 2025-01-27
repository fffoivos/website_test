import difflib

# 1. BIBLIOGRAPHY LEXICONS
# -------------------------------------------------------------------
# "Normal" forms, i.e. fully spelled words we might encounter
biblio_lexicon_normal = {
    "βιβλιογραφια",
    "βιβλιογραφ",
    "βιβλια",
    "δημοσιευσεις",
    "publications",
    "βιβλιογραφικος",   # e.g. "βιβλιογραφικός πίνακας"
    "νομολογια",
    "ελληνικη",
    "ελληνογλωσση",
    "ξενογλωσση",
}

# "Spaced" forms, if you sometimes see headings spelled character-by-character
biblio_lexicon_spaced = {
    "β ι β λ ι ο γ ρ α φ ι α",
    "β ι β λ ι ο γ ρ α φ",    # if you see partial or truncated spaced forms
    # Add more if you find them
}


# 2. FUZZY MATCH HELPER
# -------------------------------------------------------------------
def fuzzy_in_lexicon(token: str, lexicon: set[str], cutoff: int = 80) -> bool:
    """
    Returns True if 'token' is close to any string in 'lexicon'
    based on a simple similarity threshold (default 80/100).
    Uses difflib.get_close_matches under the hood.
    """
    matches = difflib.get_close_matches(token, lexicon, n=1, cutoff=cutoff / 100)
    return len(matches) > 0


# 3. CLASSIFY BIBLIOGRAPHY FUNCTION
# -------------------------------------------------------------------
def classify_bibliography(header: str) -> str | None:
    """
    Returns "BIBLIOGRAPHY" if the header likely refers to a bibliography section,
    else None.

    Rules:
      1. Normalize & split into words (assume 'normalize_greek' & 'split_words' are available).
      2. If <= 4 words:
         - If any word is a fuzzy match to biblio_lexicon_normal => "BIBLIOGRAPHY".
      3. Else if > 4 words:
         - Check if all words are single characters (spaced form).
         - If so, fuzzy match the entire line against biblio_lexicon_spaced.
      4. Otherwise => None.
    """

    # We'll call your existing normalization & splitting functions:
    norm = normalize_greek(header)       # assume you have this
    words = split_words(norm)            # assume you have this

    # CASE A: If short (4 words or fewer)
    if len(words) <= 4:
        # Check each word for fuzzy match in normal bibliography lexicon
        for w in words:
            if fuzzy_in_lexicon(w, biblio_lexicon_normal, cutoff=80):
                return "BIBLIOGRAPHY"
        return None

    # CASE B: If more than 4 words => possibly spaced-out single chars
    else:
        if all(len(w) == 1 for w in words):
            # The normalized header (with single spaces) is our "spaced form"
            spaced_form = norm
            # Fuzzy match the entire spaced string
            if fuzzy_in_lexicon(spaced_form, biblio_lexicon_spaced, cutoff=80):
                return "BIBLIOGRAPHY"
        return None


import pandas as pd
from Search_by_header import classify_bibliography

def find_bibliography_rows(input_file, output_file=None):
    """Find rows that contain bibliography headers and mark them with 'β'."""
    # Read the input CSV
    df = pd.read_csv(input_file)
    
    # Initialize label column if it doesn't exist
    if 'label' not in df.columns:
        df['label'] = ''
    
    # Counter for bibliography matches
    biblio_count = 0
    
    # Check each row's header
    for idx, row in df.iterrows():
        header = str(row['header'])
        if pd.isna(header):
            continue
            
        # Check if it's a bibliography header
        result = classify_bibliography(header)
        if result == "BIBLIOGRAPHY":
            df.at[idx, 'label'] = 'β'
            biblio_count += 1
    
    # Save results
    if output_file is None:
        output_file = input_file
    df.to_csv(output_file, index=False)
    
    print(f"Found {biblio_count} bibliography headers")
    print(f"Results saved to: {output_file}")
    
def compare_bibliography_classifications(input_file):
    """Compare bibliography classifications with existing annotations."""
    # Read the input CSV
    df = pd.read_csv(input_file)
    
    # Initialize counters
    total_rows = len(df)
    rule_based_biblio = 0
    deepseek_biblio = 0
    overlap_biblio = 0
    rule_only_biblio = 0
    deepseek_only_biblio = 0
    
    # Check each row's header
    for idx, row in df.iterrows():
        header = str(row['header'])
        if pd.isna(header):
            continue
            
        # Get rule-based classification
        is_rule_biblio = classify_bibliography(header) == "BIBLIOGRAPHY"
        
        # Get existing DeepSeek classification
        is_deepseek_biblio = row['label'] == 'β'
        
        # Update counters
        if is_rule_biblio:
            rule_based_biblio += 1
        if is_deepseek_biblio:
            deepseek_biblio += 1
        if is_rule_biblio and is_deepseek_biblio:
            overlap_biblio += 1
        if is_rule_biblio and not is_deepseek_biblio:
            rule_only_biblio += 1
        if not is_rule_biblio and is_deepseek_biblio:
            deepseek_only_biblio += 1
    
    # Print comparison results
    print("\nBibliography Classification Comparison")
    print("-" * 40)
    print(f"Total rows analyzed: {total_rows}")
    print(f"\nRule-based classifications: {rule_based_biblio}")
    print(f"DeepSeek classifications: {deepseek_biblio}")
    print(f"\nOverlapping classifications: {overlap_biblio}")
    print(f"Rule-based only: {rule_only_biblio}")
    print(f"DeepSeek only: {deepseek_only_biblio}")
    
    # Calculate agreement percentage
    total_either = rule_based_biblio + deepseek_biblio - overlap_biblio
    if total_either > 0:
        agreement_pct = (overlap_biblio / total_either) * 100
        print(f"\nAgreement percentage: {agreement_pct:.1f}%")
    
if __name__ == "__main__":
    input_file = "/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/list_rows_sections_for_annotation.csv"
    compare_bibliography_classifications(input_file)

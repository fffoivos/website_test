import unicodedata
import re
import difflib


# 1. LEXICONS
# ---------------------------------------------------------------------
# A. Table of Contents (TOC) "normal" words
toc_lexicon_normal = {
    "περιεχομενα",
    "περιεχομενο",
    # Add more variations if needed...
}

# B. Table of Contents (TOC) "spaced" words
toc_lexicon_spaced = {
    "π ε ρ ι ε χ ο μ ε ν α",
    "π ε ρ ι ε χ ο μ ε ν ο",
    # Add spaced variations here...
}

# C. Catalog "normal" words
catalog_heads_normal = {
    "πινακας",
    "καταλογος",
    # ...
}
catalog_targets_normal = {
    "σχηματων",
    "εικονων",
    "χαρτων",
    "διαγραμματων",
    # ...
}

# D. Bibliography "normal" words
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

# E. Catalog "spaced" words
# Typically, you might combine heads+targets if they appear as a single spaced phrase, 
# or keep them separate if you have headings that are exactly "π ι ν α κ α ς  σ χ η μ α τ ω ν" etc.
catalog_heads_spaced = {
    "π ι ν α κ α ς",
    "κ α τ α λ ο γ ο ς",
    # ...
}
catalog_targets_spaced = {
    "ε ι κ ο ν ω ν",
    "σ χ η μ α τ ω ν",
    "χ α ρ τ ω ν",
    "δ ι α γ ρ α μ μ α τ ω ν",
    # ...
}
# "Spaced" forms, if you sometimes see headings spelled character-by-character
biblio_lexicon_spaced = {
    "β ι β λ ι ο γ ρ α φ ι α",
    "β ι β λ ι ο γ ρ α φ",    # if you see partial or truncated spaced forms
    # Add more if you find them
}


# If you sometimes see combined forms like "π ι ν α κ α ς  ε ι κ ο ν ω ν" in a single heading,
# you could define that as well in a single set if you prefer:
catalog_combined_spaced = {
    "π ι ν α κ α ς  ε ι κ ο ν ω ν",
    "π ι ν α κ α ς  σ χ η μ α τ ω ν",
    # etc...
}







# 2. NORMALIZATION
# ---------------------------------------------------------------------
def normalize_greek(text: str) -> str:
    """
    Convert Greek text to a normalized form:
      - Lowercase
      - Strip leading/trailing whitespace
      - Remove boundary punctuation
      - Normalize diacritics (NFD → remove → NFC)
      - Also replace multiple spaces with single space
    """
    # Lowercase
    text = text.lower()

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove punctuation at boundaries (optional)
    text = re.sub(r'^[\W_]+|[\W_]+$', '', text)

    # Normalize diacritics
    text = unicodedata.normalize('NFD', text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = unicodedata.normalize('NFC', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def split_words(text: str):
    """Split on any single space (already normalized)."""
    return text.split()
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


# 3. CLASSIFIER
# ---------------------------------------------------------------------
def classify_header(header: str):
    """
    Classifies a given header string into:
      - "TOC" for Table of Contents (e.g., περιεχομενα)
      - "CATALOG" for Catalog (e.g., πίνακας/κατάλογος + στόχοι)
      - None if neither.

    Logic:
      1) Normalize the header.
      2) If 1-3 words:
         - If first word in TOC => "TOC"
         - Else if first word in heads & last word in targets => "CATALOG"
      3) Else (>3 words):
         - If all words are single-character => check if the entire normalized line
           is in the "spaced" lexicons (and if it doesn't exceed length threshold).
    """

    norm = normalize_greek(header)
    words = split_words(norm)

    # 1) Up to 3 words (short headings)
    if 1 <= len(words) <= 3:
        first_word = words[0]
        last_word = words[-1]

        # Check if first word is in normal TOC lexicon
        if first_word in toc_lexicon_normal:
            return "TOC"

        # Check if first word is in normal catalog heads
        if first_word in catalog_heads_normal:
            # and last word is in normal catalog targets
            if last_word in catalog_targets_normal:
                return "CATALOG"

        return None

    # 2) Longer headings => possibly spaced-out single characters
    else:
        # Quick check: if not all are single chars, skip
        if not all(len(w) == 1 for w in words):
            return None

        # The entire spaced-out line (already normalized + single-spaced)
        # e.g., "π ε ρ ι ε χ ο μ ε ν α" or "π ι ν α κ α ς  ε ι κ ο ν ω ν"
        spaced_form = norm

        # Ensure it's under some length threshold, say 30 chars
        if len(spaced_form) > 30:
            return None

        # 2a) Check if it matches exactly a spaced TOC form
        if spaced_form in toc_lexicon_spaced:
            return "TOC"

        # 2b) Check catalog spaced forms
        #  - Could check heads vs. targets vs. combined
        if spaced_form in catalog_heads_spaced or spaced_form in catalog_targets_spaced:
            return "CATALOG"

        # If you keep combined forms (like "π ι ν α κ α ς  ε ι κ ο ν ω ν") in a single set
        if spaced_form in catalog_combined_spaced:
            return "CATALOG"

        return None

# 4. EXAMPLE USAGE
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import pandas as pd
    import os

    # Read the input CSV file
    input_file = "/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/sections_for_annotation.csv"
    df = pd.read_csv(input_file)
    
    # Create a new dataframe for matches
    matches = []
    toc_count = 0
    catalog_count = 0
    marked_count = 0
    
    # Check each header
    for index, row in df.iterrows():
        header = str(row['header'])  # Convert to string in case of NaN
        if pd.isna(header):
            continue
            
        result = classify_header(header)
        # Keep both TOC and CATALOG matches where has_table is False
        if result in ["TOC", "CATALOG"] and not row['has_table']:
            # Add the matching row, mark with π only if section is not empty
            match_row = row.copy()
            if not pd.isna(row['section']) and str(row['section']).strip():
                match_row['label'] = 'π'
                marked_count += 1
            matches.append(match_row)
            
            if result == "TOC":
                toc_count += 1
                # Add the next four rows if they exist for TOC matches
                for next_idx in range(index + 1, min(index + 5, len(df))):
                    matches.append(df.iloc[next_idx])
            else:
                catalog_count += 1
    
    # Create matches dataframe
    matches_df = pd.DataFrame(matches)
    
    # Save to new CSV file
    output_file = "/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/header_toc.csv"
    matches_df.to_csv(output_file, index=False)
    
    print(f"Found {toc_count + catalog_count} total matches without tables:")
    print(f"- TOC matches: {toc_count} (including next 4 rows for each)")
    print(f"- CATALOG matches: {catalog_count} (no additional rows)")
    print(f"- Matches marked with π (non-empty section): {marked_count}")
    print(f"Total rows in output: {len(matches)}")
    print(f"Results saved to: {output_file}")

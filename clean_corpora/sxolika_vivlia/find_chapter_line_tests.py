import re
import unicodedata

# Regex patterns
kefalaio_atstart_pattern = re.compile(r"^(κεφαλαιο .{1,2}:?)", re.UNICODE)
kefalaio_pattern = re.compile(r"(κεφαλαιο:?)", re.UNICODE)
negative_kefalaio_pattern = re.compile(r"(κεφαλαιο[α-ω.,])", re.UNICODE)
enotita_pattern = re.compile(r".*(ενοτητα .*\d+.*)$", re.UNICODE)
negative_enotita_pattern = re.compile(r"(ενοτητα[α-ω.,])", re.UNICODE)
kef_pattern = re.compile(r".*κεφ\.\s.*", re.UNICODE)
section_number = re.compile(r"(\d\d?)\.(\d\d?)\.(\d\d?)?")

# Function to remove accents
def remove_accents(line):
    line = line.lower()
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    return accentless_line

# Function to find chapter line
def find_chapter_line(line):
    match = False
    accentless_line = remove_accents(line)
    concat_line = re.sub(r'\s', '', accentless_line)
    match = kefalaio_atstart_pattern.search(accentless_line)
    if not match and len(concat_line) < 40:
        if not negative_kefalaio_pattern.search(accentless_line):
            match = kefalaio_pattern.search(accentless_line)
        print(match, " before < 30 test")
    if not match and len(concat_line) < 30:
        print(match, " after < 30 test")
        if not negative_kefalaio_pattern.search(accentless_line): # avoids other grammatical forms such as κεφαλαιου
            print("no negative_kefalaio_pattern match")
            match = kefalaio_pattern.search(concat_line) # meant to detect "Κ Ε Φ Α Λ Α Ι Ό 8230"
        if not match and not negative_enotita_pattern.search(accentless_line):# avoids other grammatical forms such as ενοτητας
            match = enotita_pattern.search(accentless_line)
        if not match:
            match = kef_pattern.search(accentless_line)
        if not match:
            match = section_number.search(accentless_line)
    return match

# Test function to track intermediate steps and print on failure
def test_find_chapter_line(input_line):
    print(f"Original Line: {input_line}")
    print(f"Input line length: {len(input_line)}")
    
    # Run the function with the input line
    accentless_line = remove_accents(input_line)
    concat_line = re.sub(r'\s', '', accentless_line)
    match = find_chapter_line(input_line)
    
    # Print intermediate stages
    print(f"Accentless Line: {accentless_line}")
    print(f"Concatenated Line: {concat_line}")
    
    # Print the final match result
    if match:
        print(f"Regex Match: {match.group()}")
    else:
        print("No Match")
    
    # Return the match for assertion if needed
    return match

# Example test case
test_find_chapter_line("Κ Ε Φ Α Λ Α Ι Ό 8232")

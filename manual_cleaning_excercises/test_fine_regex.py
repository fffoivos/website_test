import re
import unicodedata

# Patterns
bibliography_pattern = re.compile(r".*βιβλιογραφια.*", re.UNICODE)
kefalaio_pattern = re.compile(r".*(κεφαλαιο\s.*)$", re.UNICODE)
enotita_pattern = re.compile(r".*(ενοτητα\s.*\d+)$", re.UNICODE)
kef_pattern = re.compile(r".*(κεφ\.\s.*)$", re.UNICODE)

bibliography_end_ofline = re.compile(r".*(\d+(?:\.\d+)?\s+Αναφορές\s*[-–]\s*Βιβλιογραφία)($|\n)", re.UNICODE)

chapter_heading_pattern = re.compile(r"^\s{0,3}\f?(\d{1,3})\.\d{0,3} *.{0,50}", re.UNICODE)

def find_bibliography_line(line):
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    concat_line = re.sub(r'[^α-ωΑ-Ω]', '', accentless_line)
    if len(concat_line) < 40:
        match = bibliography_pattern.search(concat_line.lower())
        if match:
            return match.group()
    match = bibliography_end_ofline.search(line.lower())
    if match:
        return match.group(1)
    return None

def find_kefalaio(line):
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    match = kefalaio_pattern.search(accentless_line.lower())
    return match.group(1) if match else None

def find_enotita(line):
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    match = enotita_pattern.search(accentless_line.lower())
    return match.group(1) if match else None

def find_kef(line):
    accentless_line = ''.join(
        c for c in unicodedata.normalize('NFD', line)
        if unicodedata.category(c) != 'Mn'
    )
    match = kef_pattern.search(accentless_line.lower())
    return match.group(1) if match else None

def find_chapter_heading(line):
    match = chapter_heading_pattern.search(line)
    return match.group() if match else None

# Test text
test_text = """
ΚΕΦΑΛΑΙΟ 5 ΙΣΤΟΡΙΚΑ ΣΤΟΙΧΕΙΑ
ΒΙΒΛΙΟΓΡΑΦΙΑ
24-0253_BOOK.indb   10
24-0253_BOOK.indb   10
13/4/2021   12:16:23 µµ
13/4/2021   12:16:23 µµ
ΚΕΦΑΛΑΙΟ 1
 
  Ενότητα 5
 
 Αρχές Προγραμματισμού Υπολογιστών1.6  Αναφορές – Βιβλιογραφία
 
 1.1
 
3.  Βασικά στοιχεία γλώσσας προγραμματισμού
  
  7.  Διαχείριση Αρχείων
"""

# Test the patterns
for line in test_text.split('\n'):
    bib_match = find_bibliography_line(line)
    if bib_match:
        print(f"Bibliography match: {bib_match}")
    
    kefalaio_match = find_kefalaio(line)
    if kefalaio_match:
        print(f"Kefalaio match: {kefalaio_match}")
    
    enotita_match = find_enotita(line)
    if enotita_match:
        print(f"Enotita match: {enotita_match}")
    
    kef_match = find_kef(line)
    if kef_match:
        print(f"Kef match: {kef_match}")
    
    chapter_heading_match = find_chapter_heading(line)
    if chapter_heading_match:
        print(f"Chapter heading match: {chapter_heading_match}")
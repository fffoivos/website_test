import pandas as pd
import json

# Define the path to the JSON input file
json_input_file = "/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/extracted_files.json"

# Load the JSON data from the file
with open(json_input_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Prepare a list to hold rows of the dataframe
rows = []

# Process each value in the dictionary
for value in data.values():
    parts = value.split(" > ")
    if len(parts) == 4:
        rows.append(parts)  # All four columns are available
    elif len(parts) == 3:
        rows.append(["-", parts[0], parts[1], parts[2]])  # Use dash for EDUCATION

# Create the dataframe with appropriate column names (translated into Greek)
df = pd.DataFrame(rows, columns=["ΕΚΠΑΙΔΕΥΣΗ", "ΣΧΟΛΕΙΟ", "ΤΑΞΗ", "ΤΙΤΛΟΣ ΒΙΒΛΙΟΥ"])

# Identify all rows where duplicates exist based on ΣΧΟΛΕΙΟ, ΤΑΞΗ, and ΤΙΤΛΟΣ ΒΙΒΛΙΟΥ (ignoring ΕΚΠΑΙΔΕΥΣΗ)
duplicates = df[df.duplicated(subset=["ΣΧΟΛΕΙΟ", "ΤΑΞΗ", "ΤΙΤΛΟΣ ΒΙΒΛΙΟΥ"], keep=False)]

# Group the duplicates by ΤΙΤΛΟΣ ΒΙΒΛΙΟΥ to print them together
if not duplicates.empty:
    grouped_duplicates = duplicates.groupby("ΤΙΤΛΟΣ ΒΙΒΛΙΟΥ")

    print(f"Αριθμός διπλότυπων τίτλων βιβλίων: {duplicates['ΤΙΤΛΟΣ ΒΙΒΛΙΟΥ'].nunique()}\n")

    # Iterate over each group and print the rows
    for title, group in grouped_duplicates:
        print(f"Διπλές εγγραφές για τον τίτλο βιβλίου: {title}")
        print(group.to_string(index=False))
        print("\n" + "-"*50 + "\n")  # Line break between groups
else:
    print("Δεν βρέθηκαν διπλοί τίτλοι βιβλίων.")

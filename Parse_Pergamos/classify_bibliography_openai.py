import pandas as pd
from openai import OpenAI
import os
import time
from typing import Optional
import concurrent.futures
from tqdm import tqdm

# Initialize DeepSeek client
client = OpenAI(
    api_key="",
    base_url="https://api.deepseek.com"
)

def create_prompt(section_text: str) -> str:
    """Create the prompt for the DeepSeek API."""
    return f"""You are a bibliography classifier for university theses. You will be given a section of text and must determine if it is a bibliography section or not. The bibliography could be in English or Greek.

Here are two truncated examples of what bibliographies look like:

Greek bibliography example:
- o Αυγελής, Ν. (2012). Εισαγωγή στη φιλοσοφία . Θεσσαλονίκη: Αντ. Σταμούλη .
- o Βοσνιάδου, Σ. (2001). Εισαγωγή στην Ψυχολογία. Αθήνα : Guntenberg.
- o Douglas , Η. R. (2003). Το εγώ της νόησης , μτφρ. Μ.Αντωνοπούλου.Αθήνα : Κάτοπτρο .
- o Kim, J. (1998). Η Φιλοσοφία του Νου , μτφρ. Ε . Μανωλακάκη , Αθήνα : Leader Books.

English/Foreign bibliography example:
- 9. Rolnik DL, Wright D, Poon LC, O'Gorman N, Syngelaki A, de Paco Matallana C, et al. Aspirin versus Placebo in Pregnancies at High Risk for Preterm Preeclampsia. N Engl J Med. 2017;377(7):613-622.
- 10. ACOG Committee Opinion No. 743: Low-Dose Aspirin Use During Pregnancy, Obstetrics & Gynecology: 2018;132(1):e44-e52
- 11. Hypertension in pregnancy: diagnosis and management NICE guideline [NG133] 2019
- 12. Ahmed A, Williams DJ, Cheed V, et al. Pravastatin for early-onset pre-eclampsia: a randomised, blinded, placebo-controlled trial. BJOG. 2020;127(4):478-488.

Note that these are truncated examples - actual bibliographies might be much longer.

Analyze the following text and respond with ONLY ONE WORD: either "bibliography" if you think it's a bibliography section, or "other" if you think it's anything else.

Text to analyze:
{section_text}

Remember: Reply with just one word - either "bibliography" or "other"."""

def classify_section(section_text: str, max_retries: int = 3) -> Optional[str]:
    """
    Classify a section of text as bibliography or other using DeepSeek's API.
    Returns 'bibliography', 'other', or None if there's an error.
    """
    if pd.isna(section_text) or not str(section_text).strip():
        return None
        
    prompt = create_prompt(section_text)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a bibliography classifier that responds with only one word."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10,
                stream=False
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # More flexible matching
            if "bibliography" in result or "βιβλιογραφία" in result:
                return "bibliography"
            elif "other" in result:
                return "other"
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            continue
    
    return None

def process_row(row):
    """Process a single row. Used for parallel processing."""
    section = str(row['section'])
    result = classify_section(section)
    return result == "bibliography"

def process_file(input_file: str, output_file: Optional[str] = None, max_workers: int = 5):
    """Process the input CSV file and classify sections using parallel processing."""
    # Read the input CSV
    df = pd.read_csv(input_file)
    
    # Initialize or reset the label column for bibliography annotations
    if 'label' not in df.columns:
        df['label'] = ''
    
    print(f"Processing {len(df)} rows with {max_workers} workers in parallel...")
    
    # Process rows in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all rows and get futures
        future_to_idx = {executor.submit(process_row, row): idx 
                        for idx, row in df.iterrows()}
        
        # Process results as they complete
        biblio_count = 0
        for future in tqdm(concurrent.futures.as_completed(future_to_idx), 
                         total=len(future_to_idx), 
                         desc="Classifying sections"):
            idx = future_to_idx[future]
            try:
                is_biblio = future.result()
                if is_biblio:
                    df.at[idx, 'label'] = 'β'
                    biblio_count += 1
            except Exception as e:
                print(f"Error processing row {idx}: {str(e)}")
    
    # Save results
    if output_file is None:
        output_file = input_file
    df.to_csv(output_file, index=False)
    
    print(f"\nFound {biblio_count} bibliography sections")
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    input_file = "/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/list_rows_sections_for_annotation.csv"
    output_file = "/home/fivos/Desktop/Parse Pergamos/well_extracted_sample_output/list_rows_sections_for_annotation.csv"
    
    print("Processing full dataset for bibliography classification...")
    print("-" * 50)
    
    # Process file with parallel workers (increased for larger dataset)
    process_file(input_file, output_file, max_workers=10)

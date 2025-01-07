from bs4 import BeautifulSoup, NavigableString
import re
import pandas as pd
from collections import Counter
from typing import Dict, Tuple

class HTMLCleaner:
    def clean_text(self, content: str) -> str:
        """Clean only <a> tags while preserving spacing and structure."""
        if not content:
            return ""
                
        soup = BeautifulSoup(content, 'html.parser')
        
        for a_tag in soup.find_all('a'):
            # Get text content without modifying its internal spacing
            text = a_tag.get_text()
            
            # Handle empty tags
            if not text.strip():
                text = ' ' if a_tag.string and ' ' in a_tag.string else ''
            else:
                # Check what comes after the tag
                next_sibling = a_tag.next_sibling
                next_char = None
                if isinstance(next_sibling, NavigableString):
                    if next_sibling.string:
                        next_char = next_sibling.string[0]
                        if not next_char in {'·', '.', ',', ';', ':', '!', '?', ')', ']', '}', ' ', '\n', '\t'}:
                            text += ' '
                
                # Check what comes before the tag
                prev_sibling = a_tag.previous_sibling
                if isinstance(prev_sibling, NavigableString):
                    if prev_sibling.string and not prev_sibling.string.endswith((' ', '\n', '\t')):
                        text = ' ' + text
            
            a_tag.replace_with(NavigableString(text))
        
        return str(soup)


    def analyze_text(self, content: str) -> Counter:
        """Count HTML tags in content."""
        if content is None:
            return Counter()
        soup = BeautifulSoup(content, 'html.parser')
        return Counter(tag.name for tag in soup.find_all())

    def process_parquet(self, input_file: str, output_file: str) -> Tuple[Dict[int, int], Dict[int, int]]:
        """Process a parquet file to clean <a> tags and analyze tag counts before and after.
        
        Args:
            input_file: Path to input parquet file
            output_file: Path to output parquet file
            
        Returns:
            Tuple of (before_counts, after_counts) where each is a dict mapping row index to <a> tag count
        """
        # Read the parquet file
        df = pd.read_parquet(input_file)
        
        # Store initial tag counts
        before_counts = df['text'].apply(lambda x: self.analyze_text(x).get('a', 0) if x is not None else 0).to_dict()
        
        # Clean texts
        df['text'] = df['text'].apply(lambda x: self.clean_text(x) if x is not None else x)
        
        # Store final tag counts
        after_counts = df['text'].apply(lambda x: self.analyze_text(x).get('a', 0) if x is not None else 0).to_dict()
        
        # Save the cleaned dataframe
        df.to_parquet(output_file)
        
        return before_counts, after_counts

def main():
    input_file = "/home/fivos/Desktop/GlossAPI_tools/scraping/wikisource/works_extractor_async_v5 copy.parquet"
    output_file = "/home/fivos/Desktop/GlossAPI_tools/scraping/wikisource/works_extractor_async_v5_copy_cleaned.parquet"
    
    cleaner = HTMLCleaner()
    before_counts, after_counts = cleaner.process_parquet(input_file, output_file)
    
    # Report any discrepancies
    print("\nAnalyzing tag cleaning results:")
    print("-" * 50)
    
    total_before = sum(before_counts.values())
    total_after = sum(after_counts.values())
    
    print(f"\nTotal <a> tags before cleaning: {total_before}")
    print(f"Total <a> tags after cleaning: {total_after}")
    
    if total_after > 0:
        print("\nRows with remaining <a> tags after cleaning:")
        for idx, count in after_counts.items():
            if count > 0:
                print(f"Row {idx}: {count} tags remaining (had {before_counts[idx]} tags before)")

if __name__ == "__main__":
    main()

import os
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Set, List, Tuple
import pandas as pd

class GreekTextProcessor:
    def __init__(self):
        self.ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        self.valid_div_types = {'textpart', 'edition'}
        
        # Valid subtypes for textpart divs
        self.valid_subtypes = {
            'chapter',
            'paragraph',
            'verse',
            'fragment',
            'section',
            'subsection',
            'line',
            'speaker',
            'epistle',
            'work',
            'episode',
            'lyric',
            'hypothesis',
            'castlist',
            'book',
            'part',
            'head'
        }
        
        # Tags to completely ignore (skip content)
        self.ignore_tags: Set[str] = {
            'note',     # Editorial notes
            'ref',      # References
            'bibl',     # Bibliography
            'foreign',  # Non-Greek text
            'figDesc',  # Figure descriptions
            'graphic',  # Graphics
            'figure',   # Figures
            'app',      # Critical apparatus
            'rdg',      # Variant readings
            'fw'        # Form work
        }
        
        # Structural formatting rules
        self.structural_rules: Dict[str, str] = {
            'lb': '\n',            # Line break
            'pb': '\n\n',          # Page break
            'cb': '\n\n',          # Column break
            'milestone': '\n\n',    # Section division
            'space': ' ',          # Space
            'p': '\n\n{}\n\n',     # Paragraph
            'l': '{}\n',          # Line of verse
            'lg': '\n{}\n',       # Line group
            'ab': '\n\n{}\n\n'    # Anonymous block
        }
        
        # Content formatting rules
        self.content_rules: Dict[str, str] = {
            'speaker': '\n{}\n',    # Speaker
            'sp': '\n{}\n',        # Speech
            'quote': '"{}"',       # Quotation
            'q': '"{}"',           # Quoted text
            'gap': '[...]',        # Gap in text
            'unclear': '[?]',      # Unclear text
            'head': '\n\n{}\n\n',  # Header
            'title': '\n{}\n\n',    # Title
            'item': '\n{}',        # List item
            'list': '\n{}\n',      # List
            'cit': '"{}"',         # Citation
            'seg': '{} ',          # Segment
            'w': '{} ',            # Word
            'num': '{}'            # Number
        }

    def is_valid_div(self, div: ET.Element) -> bool:
        """
        Check if a div element has valid type and subtype.
        Returns True if:
        1. div has type 'textpart' AND a valid subtype
        2. div has type 'edition' (no subtype check needed)
        """
        div_type = div.get('type', '')
        
        if div_type == 'edition':
            return True
            
        if div_type == 'textpart':
            subtype = div.get('subtype', '')
            return subtype in self.valid_subtypes
            
        return False

    def clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text content."""
        if text is None:
            return ''
        return ' '.join(text.split())

    def handle_special_elements(self, elem: ET.Element) -> str:
        """Handle special tags that need specific processing."""
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        if tag == 'del':
            return ''  # Skip deleted text
        elif tag == 'add':
            text = self.extract_element_text(elem)
            return f'<{text}>'  # Mark additions
        elif tag == 'supplied':
            text = self.extract_element_text(elem)
            return f'[{text}]'  # Mark supplied text
        elif tag == 'sic':
            text = self.extract_element_text(elem)
            return f'{text} [sic]'  # Mark errors
        return ''

    def handle_structural_elements(self, elem: ET.Element) -> str:
        """Handle structural tags."""
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        if tag in self.structural_rules:
            if tag in ['p', 'l', 'lg', 'ab']:
                text = self.extract_element_text(elem)
                return self.structural_rules[tag].format(text) if text.strip() else ''
            return self.structural_rules[tag]
        return ''

    def handle_content_elements(self, elem: ET.Element) -> str:
        """Handle content tags."""
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        if tag in self.content_rules:
            text = self.extract_element_text(elem)
            return self.content_rules[tag].format(text) if text.strip() else ''
        return ''

    def extract_element_text(self, elem: ET.Element) -> str:
        """Extract text from a single element."""
        if elem is None:
            return ''
        return ' '.join(''.join(elem.itertext()).split())

    def extract_text(self, elem: ET.Element) -> str:
        """Extract and format text from XML elements."""
        if elem is None:
            return ''

        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        # Skip ignored tags
        if tag in self.ignore_tags:
            return ''

        text_parts = []

        # Handle special cases
        if tag in ['del', 'add', 'supplied', 'sic']:
            return self.handle_special_elements(elem)

        # Handle structural tags
        if tag in self.structural_rules:
            return self.handle_structural_elements(elem)

        # Handle content tags
        if tag in self.content_rules:
            return self.handle_content_elements(elem)

        # Process text content
        if elem.text:
            text_parts.append(self.clean_text(elem.text))

        # Process children
        for child in elem:
            text_parts.append(self.extract_text(child))
            if child.tail:
                text_parts.append(self.clean_text(child.tail))

        return ''.join(text_parts)

    def extract_metadata(self, root: ET.Element) -> Tuple[str, str]:
        """Extract title and author from TEI header."""
        try:
            title_stmt = root.find('.//tei:titleStmt', self.ns)
            if title_stmt is not None:
                title = title_stmt.find('tei:title', self.ns)
                author = title_stmt.find('tei:author', self.ns)
                
                title_text = title.text if title is not None and title.text else "Unknown Title"
                author_text = author.text if author is not None and author.text else "Unknown Author"
                
                return title_text.strip(), author_text.strip()
            
            return "Unknown Title", "Unknown Author"
            
        except Exception as e:
            print(f"Error extracting metadata: {str(e)}")
            return "Unknown Title", "Unknown Author"

    def process_file(self, input_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """Process a single XML file and return the extracted text and metadata."""
        try:
            tree = ET.parse(input_path)
            root = tree.getroot()
            
            # Extract metadata
            title, author = self.extract_metadata(root)
            
            # Find all divs and filter for valid types and subtypes
            valid_divs = []
            for div in root.findall('.//tei:div', self.ns):
                if self.is_valid_div(div):
                    valid_divs.append(div)
            
            if not valid_divs:
                return False, "No valid div types/subtypes found", None

            # Extract text from each valid div
            extracted_texts = []
            for div in valid_divs:
                extracted_texts.append(self.extract_text(div))

            # Combine and clean text
            combined_text = '\n'.join(extracted_texts)
            
            # Clean up multiple blank lines
            lines = [line.strip() for line in combined_text.splitlines()]
            cleaned_lines = []
            empty_line_count = 0
            
            for line in lines:
                if line:
                    empty_line_count = 0
                    cleaned_lines.append(line)
                elif empty_line_count < 2:
                    empty_line_count += 1
                    cleaned_lines.append('')
            
            cleaned_text = '\n'.join(cleaned_lines)
            
            return True, "Success", {
                'title': title,
                'author': author,
                'text': cleaned_text
            }
            
        except Exception as e:
            return False, str(e), None


def process_corpus(root_dir: str, output_dir: str) -> None:
    """Process the entire corpus of Greek texts."""
    processor = GreekTextProcessor()
    processed_count = 0
    error_count = 0
    empty_count = 0
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # List to store all book data
    books_data = []
    
    # Process files
    for root, _, files in os.walk(root_dir):
        for filename in files:
            if filename.endswith('.xml') and 'grc' in filename:
                input_path = os.path.join(root, filename)
                
                success, message, data = processor.process_file(input_path)
                
                if success and data is not None:
                    processed_count += 1
                    
                    # Add to books data
                    books_data.append({
                        'index': processed_count,
                        'author': data['author'],
                        'title': data['title'],
                        'book_text': data['text']
                    })
                    
                    # Save text file
                    output_path = os.path.join(output_dir, f'1k_book_{processed_count}.txt')
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(data['text'])
                    
                    if processed_count % 100 == 0:
                        print(f"Processed {processed_count} files...")
                else:
                    if "No valid div types found" in message:
                        empty_count += 1
                        print(f"No valid divs in: {input_path}")
                    else:
                        error_count += 1
                        print(f"Error in {input_path}: {message}")
    
    # Create DataFrame and save to parquet
    if books_data:
        df = pd.DataFrame(books_data)
        parquet_path = os.path.join(output_dir, 'first1k_books.parquet')
        df.to_parquet(parquet_path, index=False)
        
        # Also save a CSV with just metadata for easy viewing
        metadata_df = df[['index', 'author', 'title']]
        csv_path = os.path.join(output_dir, 'first1k_books_metadata.csv')
        metadata_df.to_csv(csv_path, index=False)

    print(f"\nProcessing complete:")
    print(f"Successfully processed: {processed_count} files")
    print(f"Files without valid divs: {empty_count} files")
    print(f"Errors encountered: {error_count} files")
    print(f"\nOutputs saved:")
    print(f"- Individual text files: {output_dir}/1k_book_*.txt")
    print(f"- Complete dataset: {output_dir}/first1k_books.parquet")
    print(f"- Metadata summary: {output_dir}/first1k_books_metadata.csv")

if __name__ == "__main__":
    root_directory = "/home/fivos/Desktop/First1KGreek_fork/data"
    output_directory = "/home/fivos/Desktop/First1KGreek_fork/extracted_texts"
    process_corpus(root_directory, output_directory)
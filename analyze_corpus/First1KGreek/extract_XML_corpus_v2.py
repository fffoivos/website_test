import os
import csv
from lxml import etree
from typing import Set, Optional, Tuple, List
import logging
import re
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction_v2.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class XMLTextExtractor:
    def __init__(self):
        # Tags to completely ignore (remove with their content)
        self.ignore_tags = {
            'note', 'bibl', 'figDesc', 'graphic', 'figure', 'app', 
            'rdg', 'fw', 'back', 'teiHeader', 'milestone', 'label'
        }
        self.namespaces = {
            'tei': 'http://www.tei-c.org/ns/1.0',
            'default': ''
        }

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and normalizing spacing."""
        # Clean up multiple spaces within lines
        lines = [' '.join(line.split()) for line in text.split('\n')]
        # Join with original newlines to preserve spacing
        return '\n'.join(lines)

    def extract_text_from_element(self, element: etree._Element) -> str:
        """Extract text from an element and its children."""
        if not isinstance(element.tag, str):
            return ''
            
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        if tag in self.ignore_tags:
            return ''

        text_parts = []
        
        # Add element's direct text
        if element.text:
            text_parts.append(element.text)
        
        # Process children
        for child in element:
            if not isinstance(child.tag, str):
                continue
                
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            # For ignored tags (like notes), we skip the tag but keep its tail
            if child_tag in self.ignore_tags:
                if child.tail:
                    text_parts.append(child.tail)
                continue
            
            # Get child's text
            child_text = self.extract_text_from_element(child)
            if child_text:
                # Handle different tag types
                if child_tag in ['div', 'p']:
                    # Add double newlines for divs and paragraphs
                    if text_parts and not text_parts[-1].endswith('\n\n'):
                        text_parts.append('\n\n')
                    text_parts.append(child_text)
                    if not child_text.endswith('\n\n'):
                        text_parts.append('\n\n')
                elif child_tag == 'l':
                    # Single newline for poetry lines
                    if text_parts and not text_parts[-1].endswith('\n'):
                        text_parts.append('\n')
                    text_parts.append(child_text.rstrip())
                    text_parts.append('\n')
                else:
                    # For other tags, just add the text
                    text_parts.append(child_text)
            
            # Add tail text
            if child.tail:
                text_parts.append(child.tail)

        result = ''.join(text_parts)
        # Clean up multiple newlines while preserving doubles
        result = re.sub(r'\n{3,}', '\n', result)
        return result.strip()

    def extract_text_from_xml(self, xml_file: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract text content and metadata from XML file."""
        try:
            parser = etree.XMLParser(recover=True, encoding='utf-8')
            tree = etree.parse(xml_file, parser)
            root = tree.getroot()

            # Determine format
            is_tei2 = root.tag == 'TEI.2'
            ns = None if is_tei2 else {'tei': 'http://www.tei-c.org/ns/1.0'}
            
            # Extract author and title
            if is_tei2:
                title_elems = root.xpath('.//title[not(@type="sub")]')
                author_elems = root.xpath('.//author')
            else:
                title_elems = root.xpath('.//tei:titleStmt/tei:title[not(@type="sub")]', namespaces=ns)
                author_elems = root.xpath('.//tei:titleStmt/tei:author', namespaces=ns)
            
            # Get title
            title = title_elems[0].text.strip() if title_elems else None
            
            # Get author - try different paths
            author = None
            if author_elems:
                author = author_elems[0].text
                if author:
                    author = author.strip()
            
            # If no author found, try to extract from filename
            if not author:
                # Extract TLG number from filename
                basename = os.path.basename(xml_file)
                tlg_match = re.match(r'tlg(\d+)\.', basename)
                if tlg_match:
                    tlg_num = tlg_match.group(1)
                    # You could maintain a mapping of TLG numbers to authors
                    # For now, we'll keep it as Unknown
                    author = "Unknown"

            # Extract text
            text_parts = []
            
            # Find the main text content
            if is_tei2:
                # For TEI.2 format
                main_divs = root.xpath('.//div1 | .//div2')
                for div in main_divs:
                    text = self.extract_text_from_element(div)
                    if text.strip():
                        text_parts.append(text)
            else:
                # For TEI format, start with div[@type="edition"]
                edition_divs = root.xpath('.//tei:div[@type="edition"]', namespaces=ns)
                if edition_divs:
                    for div in edition_divs:
                        text = self.extract_text_from_element(div)
                        if text.strip():
                            text_parts.append(text)
                else:
                    # Fallback: look for any text-containing elements
                    for elem in root.xpath('.//tei:p | .//tei:l | .//tei:div[@type="textpart"]', namespaces=ns):
                        text = self.extract_text_from_element(elem)
                        if text.strip():
                            text_parts.append(text)

            text_content = self.clean_text('\n'.join(text_parts))
            
            if text_content:
                logging.info(f"Successfully extracted text (length: {len(text_content)} characters)")
            else:
                logging.warning("No text content was extracted")

            return author, title, text_content

        except Exception as e:
            logging.error(f"Error parsing {xml_file}: {str(e)}")
            return None, None, None

def process_files(input_folder: str, output_folder: str, csv_output: str):
    """Process all Greek XML files and write extracted text to output folder."""
    extractor = XMLTextExtractor()
    metadata = []
    stats = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'total_chars': 0
    }

    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Find all XML files recursively
    for root, _, files in os.walk(input_folder):
        for file in files:
            # Only process Greek texts and skip files starting with _
            if (file.endswith('.xml') and 'grc' in file 
                and not file.startswith('_')):
                input_path = os.path.join(root, file)
                stats['total_files'] += 1

                try:
                    # Extract text and metadata
                    author, title, text = extractor.extract_text_from_xml(input_path)
                    
                    if text:
                        # Create output filename (just the base name)
                        file_name = os.path.splitext(file)[0] + '.txt'
                        output_path = os.path.join(output_folder, file_name)
                        
                        # Write text to file
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(text)
                        
                        # Update statistics
                        stats['successful'] += 1
                        stats['total_chars'] += len(text)
                        
                        # Add metadata
                        metadata.append({
                            'input_file': input_path,
                            'output_file': output_path,
                            'author': author,
                            'title': title,
                            'char_count': len(text)
                        })
                        
                        logging.info(f"Successfully processed {input_path} -> {output_path}")
                    else:
                        stats['failed'] += 1
                        logging.warning(f"No text extracted from {input_path}")
                
                except Exception as e:
                    stats['failed'] += 1
                    logging.error(f"Error processing {input_path}: {str(e)}")

    # Write metadata to CSV
    if metadata:
        with open(csv_output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['input_file', 'output_file', 'author', 'title', 'char_count'])
            writer.writeheader()
            writer.writerows(metadata)

    # Log final statistics
    logging.info(f"\nProcessing Complete!\n"
                f"Total files processed: {stats['total_files']}\n"
                f"Successfully processed: {stats['successful']}\n"
                f"Failed: {stats['failed']}\n"
                f"Total characters extracted: {stats['total_chars']}\n"
                f"Average characters per file: {stats['total_chars']/stats['successful'] if stats['successful'] > 0 else 0:.2f}")

    return metadata

def main():
    """Main entry point of the script."""
    input_folder = '/home/fivos/Desktop/canonical-greekLit/data/'
    output_folder = '/home/fivos/Desktop/canonical-greekLit/Classics_extracted_text_v3'
    csv_output = '/home/fivos/Desktop/canonical-greekLit/Classics_metadata.csv'
    
    try:
        process_files(input_folder, output_folder, csv_output)
        logging.info("Processing completed successfully")
    except Exception as e:
        logging.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    main()

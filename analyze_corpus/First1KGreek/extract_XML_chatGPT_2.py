import os
import csv
from lxml import etree
from typing import Set, Optional, Tuple, List
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class XMLTextExtractor:
    def __init__(self):
        self.valid_div_types = {'textpart', 'edition'}
        self.valid_subtypes = {
            'chapter', 'paragraph', 'verse', 'fragment', 'section', 'subsection',
            'line', 'speaker', 'epistle', 'work', 'episode', 'lyric',
            'hypothesis', 'castlist', 'book', 'part', 'head'
        }
        self.ignore_tags = {
            'note', 'ref', 'bibl', 'foreign', 'figDesc', 'graphic',
            'figure', 'app', 'rdg', 'fw', 'back', 'teiHeader', 'milestone'
        }
        self.namespace = {'tei': 'http://www.tei-c.org/ns/1.0'}
        
    def is_valid_div(self, div_elem: etree._Element) -> bool:
        """
        Check if a div element meets the criteria for text extraction.
        
        Args:
            div_elem: The div element to check
            
        Returns:
            bool: True if the div is valid for extraction
        """
        div_type = div_elem.get('type')
        div_subtype = div_elem.get('subtype')
        
        if div_type in self.valid_div_types:
            return True
        if div_subtype in self.valid_subtypes:
            return True
        return False

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text while preserving empty lines and structure.
        
        Args:
            text: The text to clean
            
        Returns:
            str: Cleaned text with preserved structure
        """
        if not text:
            return ""
        
        # Split into lines and clean each line individually
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Replace multiple spaces with single space
            cleaned_line = ' '.join(line.split())
            cleaned_lines.append(cleaned_line)
        
        # Join lines back together, preserving empty lines
        return '\n'.join(line.strip() for line in cleaned_lines)

    def extract_text_from_element(self, element: etree._Element) -> str:
        """
        Recursively extract text from an element, skipping ignored tags.
        
        Args:
            element: The XML element to process
            
        Returns:
            str: Extracted text with preserved structure
        """
        text_parts = []
        
        # Handle the text directly attached to this element
        if element.text and element.text.strip():
            text_parts.append(element.text.strip())

        # Process child elements
        for child in element:
            # Skip ignored tags and their content
            if child.tag.split('}')[-1] in self.ignore_tags:
                continue
                
            # Recursively process valid child elements
            child_text = self.extract_text_from_element(child)
            if child_text:
                text_parts.append(child_text)
                
            # Handle text that follows the child element
            if child.tail and child.tail.strip():
                text_parts.append(child.tail.strip())

        return ' '.join(text_parts)

    def extract_text_from_xml(self, xml_file: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract text content and metadata from XML file.
        
        Args:
            xml_file: Path to the XML file
            
        Returns:
            Tuple containing (author, title, text_content), or (None, None, None) if extraction fails
        """
        try:
            parser = etree.XMLParser(recover=True, encoding='utf-8')
            tree = etree.parse(xml_file, parser)
            root = tree.getroot()

            # Extract author
            author_elems = root.xpath('.//tei:author', namespaces=self.namespace)
            author = author_elems[0].text.strip() if author_elems else 'Unknown'

            # Extract title
            title_elems = root.xpath('.//tei:titleStmt/tei:title', namespaces=self.namespace)
            title = title_elems[0].text.strip() if title_elems else 'Unknown'

            # Extract text content from valid divs
            div_elems = root.xpath('.//tei:text/tei:body/tei:div[@type="edition"]//tei:div', namespaces=self.namespace)
            
            logging.info(f"\nProcessing file: {xml_file}")
            logging.info(f"Found {len(div_elems)} div elements")
            
            text_parts = []

            for div in div_elems:
                # Print div hierarchy information
                ancestor_divs = div.xpath('ancestor::tei:div', namespaces=self.namespace)
                depth = len(ancestor_divs)
                
                logging.info(f"\nDiv at depth {depth}")
                logging.info(f"Type: {div.get('type')}")
                logging.info(f"Subtype: {div.get('subtype')}")
                logging.info(f"N: {div.get('n')}")
                
                # Get a sample of the text content
                sample_text = self.extract_text_from_element(div)[:100] if self.extract_text_from_element(div) else "No text"
                logging.info(f"Text sample: {sample_text}...")
                
                if self.is_valid_div(div):
                    logging.info("This div was validated and will be extracted")
                    div_text = self.extract_text_from_element(div)
                    if div_text:
                        text_parts.append(div_text)

            # Join all text parts with double newlines to preserve structure
            text_content = '\n\n'.join(text_parts) if text_parts else ''
            text_content = self.clean_text(text_content)

            if text_content:
                logging.info(f"Successfully extracted text (length: {len(text_content)} characters)")
            else:
                logging.warning("No text content was extracted")

            return author, title, text_content

        except Exception as e:
            logging.error(f"Error parsing {xml_file}: {str(e)}")
            return None, None, None

def process_files(input_folder: str, output_folder: str, csv_output: str):
    """
    Process all XML files in the input folder and generate output files.
    
    Args:
        input_folder: Path to the folder containing input XML files
        output_folder: Path where output text files should be saved
        csv_output: Path where the metadata CSV should be saved
    """
    extractor = XMLTextExtractor()
    data = []
    index = 1
    
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    # Calculate maximum depth to traverse
    max_depth = Path(input_folder).resolve().parts.__len__() + 2

    # Process all files
    for root_dir, sub_dirs, files in os.walk(input_folder):
        current_depth = Path(root_dir).resolve().parts.__len__()
        if current_depth > max_depth:
            del sub_dirs[:]  # Don't traverse deeper
        
        logging.info(f"Processing directory: {root_dir}")
        
        for file_name in files:
            if not file_name.startswith('_') and 'grc' in file_name and file_name.endswith('.xml'):
                logging.info(f"Processing file: {file_name}")
                xml_file_path = os.path.join(root_dir, file_name)
                
                try:
                    author, title, text_content = extractor.extract_text_from_xml(xml_file_path)
                    
                    if text_content:
                        # Write text content to .txt file
                        txt_file_name = os.path.splitext(file_name)[0] + '.txt'
                        txt_file_path = os.path.join(output_folder, txt_file_name)
                        
                        with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                            txt_file.write(text_content)
                        
                        # Append to data list for CSV
                        data.append({
                            'index': index,
                            'author': author,
                            'title': title,
                            'filename': file_name,
                            'original_path': xml_file_path,
                            'extracted_path': txt_file_path
                        })
                        index += 1
                        logging.info(f"Successfully processed {file_name}")
                    else:
                        logging.warning(f"No valid text content found in {file_name}")
                
                except Exception as e:
                    logging.error(f"Error processing {file_name}: {str(e)}")
            else:
                logging.debug(f"Skipping file: {file_name}")

    # Write data to CSV file
    if data:
        csv_columns = ['index', 'author', 'title', 'filename', 'original_path', 'extracted_path']
        try:
            with open(csv_output, 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                for entry in data:
                    writer.writerow(entry)
            logging.info(f"CSV file created at {csv_output}")
        except Exception as e:
            logging.error(f"Error writing CSV file: {str(e)}")
    else:
        logging.warning("No data to write to CSV.")

def main():
    """Main entry point of the script."""
    # Configure these paths as needed
    input_folder = '/home/fivos/Desktop/First1KGreek_fork/data/tlg0018/tlg001'
    output_folder = '/home/fivos/Desktop/First1KGreek_fork/extracted_sample_v4_test'
    csv_output = '/home/fivos/Desktop/First1KGreek_fork/extracted_sample_v4_test/1k_metadata.csv'
    
    try:
        process_files(input_folder, output_folder, csv_output)
        logging.info("Processing completed successfully")
    except Exception as e:
        logging.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    main()